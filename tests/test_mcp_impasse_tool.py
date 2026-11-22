import pytest

from mcp_server.server import create_server
from src.graph import builder as graph_module
from src.recipe_session import RecipeSession
from src.mcp_client import McpToolClient, McpToolError
from src.schemas import Recipe, SubChefEvaluation
from src.state import RecipeState, create_initial_state


pytestmark = pytest.mark.usefixtures("stub_cook_llm")

THREAD_ID = "thread-1"


def create_recipe() -> Recipe:
    return Recipe(
        dough="Potato dough",
        filling="Chicken",
        ingredients=["potato", "chicken"],
        preparation="Boil the potatoes and shape the dough.",
        utensils=["pot"],
        preparation_methods=["boiling"],
    )


def paused_session(monkeypatch, decisions):
    """Cria uma conversa parada no Impasse, com Chef e SubChef simulados."""
    calls = {"subchef": 0}

    def fake_chef_node(state: RecipeState) -> dict[str, object]:
        recipe = create_recipe()
        recipe.ingredients.extend(state.get("ingredient_additions", []))
        return {
            "recipe": recipe,
            "recipe_version": state["recipe_version"] + 1,
        }

    def fake_subchef_node(state: RecipeState) -> dict[str, object]:
        calls["subchef"] += 1
        decision = decisions[calls["subchef"] - 1]
        return {
            "subchef_evaluation": SubChefEvaluation(
                decision=decision,
                critique="Revise the proposal." if decision == "rejected" else "",
            )
        }

    monkeypatch.setattr(graph_module, "chef_node", fake_chef_node)
    monkeypatch.setattr(graph_module, "subchef_node", fake_subchef_node)

    session = RecipeSession()
    paused = session.start(
        create_initial_state("Make a coxinha.", THREAD_ID, max_revisions=2)
    )
    assert paused["status"] == "awaiting_user"
    return session


def record(session, **overrides):
    arguments = {
        "thread_id": THREAD_ID,
        "action": "save",
        "expected_state_version": 0,
        "idempotency_key": "key-1",
        "ingredient_additions": ["cheese"],
    }
    arguments.update(overrides)
    client = McpToolClient(create_server(session=session))
    return client.call("record_impasse_decision", arguments)


def test_save_keeps_the_session_paused_and_bumps_the_version(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])

    outcome = record(session)

    assert outcome == {
        "thread_id": THREAD_ID,
        "status": "awaiting_user",
        "user_action": "save",
        "state_version": 1,
        "revision_count": 2,
        "total_attempts": 2,
        "recipe_version": 2,
    }


def test_outcome_does_not_expose_the_full_state(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])

    outcome = record(session)

    assert "recipe" not in outcome
    assert "messages" not in outcome


def test_stale_version_is_a_conflict_and_reports_both_versions(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])
    record(session)

    with pytest.raises(McpToolError) as error:
        record(session, idempotency_key="key-2", expected_state_version=0)

    assert error.value.code == "state_version_conflict"
    assert error.value.details == {"expected": 0, "current": 1}


def test_repeating_the_same_decision_returns_the_original_result(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])

    first = record(session)
    second = record(session)

    assert second == first
    assert second["state_version"] == 1


def test_reusing_a_key_with_a_different_decision_is_rejected(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])
    record(session)

    with pytest.raises(McpToolError) as error:
        record(session, ingredient_additions=["rice"])

    assert error.value.code == "idempotency_key_reuse"


def test_unknown_conversation_is_not_found(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])

    with pytest.raises(McpToolError) as error:
        record(session, thread_id="unknown")

    assert error.value.code == "workflow_not_found"


def test_decision_after_cancel_is_not_paused(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])

    cancelled = record(
        session,
        action="cancel",
        idempotency_key="cancel-1",
        ingredient_additions=None,
    )
    assert cancelled["status"] == "cancelled"

    with pytest.raises(McpToolError) as error:
        record(
            session,
            expected_state_version=1,
            idempotency_key="key-2",
        )

    assert error.value.code == "workflow_not_paused"


def test_save_without_ingredients_or_guidance_is_invalid(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])

    with pytest.raises(McpToolError) as error:
        record(session, ingredient_additions=None)

    assert error.value.code == "invalid_input"
    assert error.value.details["errors"]


def test_unknown_action_is_invalid_input(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected"])

    with pytest.raises(McpToolError) as error:
        record(session, action="approve")

    assert error.value.code == "invalid_input"


def test_resume_continues_the_graph_to_completion(monkeypatch):
    session = paused_session(monkeypatch, ["rejected", "rejected", "approved"])

    outcome = record(
        session,
        action="resume",
        ingredient_additions=["cheese"],
    )

    assert outcome["status"] == "completed"
    assert outcome["total_attempts"] == 3
    assert outcome["revision_count"] == 1
    final_state = session.get_state(THREAD_ID)
    assert final_state["final_response"]["recipe"]["title"]
    assert final_state["final_response"]["image"]["status"] == "generated"


def test_resume_saves_recipe_in_session_history_and_retry_keeps_one_entry(monkeypatch):
    """Confere que retomar pelo MCP salva a receita uma vez na sessão."""
    session = paused_session(monkeypatch, ["rejected", "rejected", "approved"])

    first = record(session, action="resume", ingredient_additions=["cheese"])
    second = record(session, action="resume", ingredient_additions=["cheese"])

    recipes = session.history.list_recipes()
    assert first == second
    assert first["status"] == "completed"
    assert len(recipes) == 1
    assert recipes[0]["id"] == THREAD_ID
    assert recipes[0]["recipe"] == session.get_state(THREAD_ID)["final_response"]["recipe"]


def test_save_and_cancel_do_not_add_recipes_to_session_history(monkeypatch):
    """Confere que salvar ou encerrar o impasse mantém o histórico vazio."""
    session = paused_session(monkeypatch, ["rejected", "rejected"])

    record(session)
    record(
        session,
        action="cancel",
        expected_state_version=1,
        idempotency_key="cancel-history",
        ingredient_additions=None,
    )

    assert session.history.list_recipes() == []
