from unittest.mock import Mock

from langchain_core.runnables import RunnableLambda
import pytest

from src.graph import builder as graph_module
from src.graph.nodes import health
from src.schemas import Recipe, SubChefEvaluation
from src.state import RecipeState, create_initial_state


pytestmark = pytest.mark.usefixtures("stub_cook_llm")


def create_recipe() -> Recipe:
    """Cria uma proposta fixa para os testes do grafo."""
    return Recipe(
        dough="Potato dough",
        filling="Chicken",
        ingredients=["potato", "chicken"],
        preparation="Boil the potatoes and shape the dough.",
        utensils=["pot"],
        preparation_methods=["boiling"],
    )


def build_test_graph(monkeypatch, decisions):
    """Monta o grafo com Chef e SubChef simulados."""
    calls = {"chef": 0, "subchef": 0}

    def fake_chef_node(state: RecipeState) -> dict[str, object]:
        """Devolve uma proposta e avança a versão da receita."""
        calls["chef"] += 1
        return {
            "recipe": create_recipe(),
            "recipe_version": state["recipe_version"] + 1,
        }

    def fake_subchef_node(state: RecipeState) -> dict[str, object]:
        """Devolve a próxima decisão programada para o cenário."""
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

    return graph_module.build_graph(), calls


def test_approval_on_first_attempt_completes_recipe(monkeypatch, stub_cook_llm):
    """Verifica que a primeira aprovação produz uma receita finalizada."""
    workflow, calls = build_test_graph(monkeypatch, ["approved"])
    initial_state = create_initial_state("Make a coxinha.", "thread-1")

    result = workflow.invoke(initial_state)

    assert result["status"] == "completed"
    assert result["final_response"]["recipe"]["title"] == "Crocância de Frango"
    assert result["final_response"]["recipe"]["ingredients"] == [
        "potato",
        "chicken",
    ]
    assert result["final_response"]["recipe"]["steps"] == [
        "Cozinhe as batatas.",
        "Modele a massa.",
    ]
    assert result["revision_count"] == 1
    assert result["total_attempts"] == 1
    assert result["recipe_version"] == 1
    assert calls == {"chef": 1, "subchef": 1}
    stub_cook_llm.assert_called_once()


def test_rejection_then_approval_revises_and_finishes(monkeypatch):
    """Verifica que uma rejeição seguida de aprovação conclui a receita."""
    workflow, calls = build_test_graph(monkeypatch, ["rejected", "approved"])
    initial_state = create_initial_state(
        "Make a coxinha.",
        "thread-1",
        max_revisions=2,
    )

    result = workflow.invoke(initial_state)

    assert result["status"] == "completed"
    assert result["revision_count"] == 2
    assert result["total_attempts"] == 2
    assert result["recipe_version"] == 2
    assert calls == {"chef": 2, "subchef": 2}


def test_rejection_on_last_attempt_ends_at_impasse(monkeypatch, stub_cook_llm):
    """Verifica que esgotar as avaliações leva ao Impasse."""
    workflow, calls = build_test_graph(monkeypatch, ["rejected", "rejected"])
    initial_state = create_initial_state(
        "Make a coxinha.",
        "thread-1",
        max_revisions=2,
    )

    result = workflow.invoke(initial_state)

    assert result["status"] == "awaiting_user"
    assert "final_response" not in result
    assert result["revision_count"] == 2
    assert result["total_attempts"] == 2
    assert result["recipe_version"] == 2
    assert calls == {"chef": 2, "subchef": 2}
    stub_cook_llm.assert_not_called()


def test_approval_on_last_attempt_is_not_blocked_by_limit(monkeypatch):
    """Verifica que a aprovação na última avaliação conclui a receita."""
    workflow, calls = build_test_graph(monkeypatch, ["approved"])
    initial_state = create_initial_state(
        "Make a coxinha.",
        "thread-1",
        max_revisions=1,
    )

    result = workflow.invoke(initial_state)

    assert result["status"] == "completed"
    assert result["revision_count"] == 1
    assert result["total_attempts"] == 1
    assert calls == {"chef": 1, "subchef": 1}


def test_technical_subchef_failure_does_not_record_attempt(monkeypatch):
    """Verifica que uma falha técnica no SubChef não conta como avaliação."""

    def fake_chef_node(state: RecipeState) -> dict[str, object]:
        """Devolve a proposta que chega ao SubChef antes da falha."""
        return {
            "recipe": create_recipe(),
            "recipe_version": state["recipe_version"] + 1,
        }

    monkeypatch.setattr(graph_module, "chef_node", fake_chef_node)
    monkeypatch.setattr(
        graph_module,
        "subchef_node",
        Mock(side_effect=RuntimeError("LLM request failed.")),
    )
    record_review = Mock(wraps=graph_module.record_review_node)
    monkeypatch.setattr(graph_module, "record_review_node", record_review)

    workflow = graph_module.build_graph()
    initial_state = create_initial_state("Make a coxinha.", "thread-1")

    with pytest.raises(RuntimeError, match="LLM request failed"):
        workflow.invoke(initial_state)

    record_review.assert_not_called()
    assert initial_state["revision_count"] == 0
    assert initial_state["total_attempts"] == 0


def stub_health(monkeypatch, *, advice=None, error=None, results=None):
    """Configura a busca e o modelo simulados do nó de saúde."""
    monkeypatch.setattr(health, "HEALTH_SEARCH", lambda query: list(results or []))

    def respond(_prompt):
        """Devolve o aviso programado ou simula uma falha técnica."""
        if error is not None:
            raise error
        return advice

    model = Mock()
    model.with_structured_output.return_value = RunnableLambda(respond)
    monkeypatch.setattr(health, "call_llm", Mock(return_value=model))


def test_health_advice_appears_in_final_response(monkeypatch):
    """Verifica que o aviso de saúde chega em final_response["health"]."""
    workflow, _ = build_test_graph(monkeypatch, ["approved"])
    stub_health(
        monkeypatch,
        results=[
            {"title": "Fonte A", "url": "https://example.test/a", "content": "trecho"}
        ],
        advice={
            "health_warning": "Aviso culinário não oficial.",
            "contraindications": ["Consumo em excesso."],
            "sources_used": [{"title": "Fonte A", "url": "https://example.test/a"}],
            "uncertainty": "Confiança média nas fontes simuladas.",
        },
    )

    result = workflow.invoke(create_initial_state("Make a coxinha.", "thread-1"))

    health_response = result["final_response"]["health"]
    assert result["status"] == "completed"
    assert health_response["health_status"] == "ok"
    assert health_response["warning"] == "Aviso culinário não oficial."
    assert health_response["contraindications"] == ["Consumo em excesso."]
    assert health_response["sources"] == [
        {"title": "Fonte A", "url": "https://example.test/a"}
    ]


def test_recipe_completes_when_health_advice_is_unavailable(monkeypatch):
    """Verifica que uma falha no aviso de saúde não impede a conclusão."""
    workflow, _ = build_test_graph(monkeypatch, ["approved"])
    stub_health(monkeypatch, error=RuntimeError("LLM request failed."))

    result = workflow.invoke(create_initial_state("Make a coxinha.", "thread-1"))

    health_response = result["final_response"]["health"]
    assert result["status"] == "completed"
    assert health_response["health_status"] == "unavailable"
    assert health_response["warning"] is None
    assert health_response["contraindications"] == []
    assert result["final_response"]["recipe"]["ingredients"] == [
        "potato",
        "chicken",
    ]


def test_health_runs_after_cook_and_before_finalize(monkeypatch):
    """Verifica a ordem Cozinheiro → Saúde → Finalização."""
    seen = {}

    def tracking_health_node(state: RecipeState) -> dict[str, object]:
        """Registra o que já existe no estado quando o nó de saúde roda."""
        seen["cook_output"] = "cook_output" in state
        seen["final_response"] = "final_response" in state
        return health.health_node(state)

    monkeypatch.setattr(graph_module, "health_node", tracking_health_node)
    workflow, _ = build_test_graph(monkeypatch, ["approved"])

    result = workflow.invoke(create_initial_state("Make a coxinha.", "thread-1"))

    assert seen == {"cook_output": True, "final_response": False}
    assert result["status"] == "completed"
    assert result["final_response"]["health"]["health_status"] == "insufficient"