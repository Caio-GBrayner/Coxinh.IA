"""O Impasse nunca prende a conversa: texto livre, comparação tolerante, falhas e limite."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.api.app import create_app
from src.graph import builder as graph_module
from src.graph.impasse import ImpasseDecision, ResumeLimitReached
from src.graph.nodes.subchef import subchef_node
from src.graph.resource_validation import validate_recipe_resources
from src.graph.workflow import RECOVERY_MESSAGE
from src.recipe_session import RecipeSession
from src.schemas import Recipe, SubChefEvaluation
from src.state import create_initial_state
from src.utils.ingredients import mentions, split_items
from tests import fakes


pytestmark = pytest.mark.usefixtures("stub_cook_llm")


def decision(action, version, key, **extra):
    return ImpasseDecision(
        action=action, expected_state_version=version, idempotency_key=key, **extra
    )


def recipe(ingredients, utensils=(), methods=("fritar",)):
    return Recipe(
        dough="massa",
        filling="recheio",
        ingredients=list(ingredients),
        preparation="Frite.",
        utensils=list(utensils),
        preparation_methods=list(methods),
    )


# --- Texto livre -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("queijo, carne e fogão", ["queijo", "carne", "fogão"]),
        ("queijo; carne\nmassa de mandioca", ["queijo", "carne", "massa de mandioca"]),
        ("- pão\n* manteiga\n1. ovo\n2) leite", ["pão", "manteiga", "ovo", "leite"]),
        ("Queijo, queijo,  QUEIJO ", ["Queijo"]),
        (["queijo, carne", "carne", "  "], ["queijo", "carne"]),
        (",, ;\n", []),
    ],
)
def test_split_items_accepts_free_text(text, expected):
    assert split_items(text) == expected


def test_mentions_ignores_accents_case_and_partial_names():
    assert mentions("pao", "Pão francês")
    assert mentions("queijo", "queijo ralado")
    assert mentions("carne moída", "carne")
    assert not mentions("sal", "salsa")


def test_decision_splits_free_text_and_still_rejects_empty_save():
    parsed = decision("save", 0, "k", ingredient_additions="queijo, carne e fogão")
    assert parsed.ingredient_additions == ["queijo", "carne", "fogão"]

    with pytest.raises(ValidationError):
        decision("save", 0, "k", ingredient_additions=" , ;")


# --- Comparação tolerante --------------------------------------------------------


def test_additions_count_in_ingredients_utensils_and_methods():
    result = validate_recipe_resources(
        recipe(["Pão francês", "queijo ralado"], utensils=["fogão a lenha"]),
        authorized_ingredients=None,
        authorized_utensils=None,
        authorized_preparation_methods=None,
        ingredient_additions=["pao", "queijo", "fogão"],
    )
    assert result.missing_ingredient_additions == []


def test_old_additions_saved_together_are_split_before_checking():
    result = validate_recipe_resources(
        recipe(["queijo", "carne"]),
        authorized_ingredients=None,
        authorized_utensils=None,
        authorized_preparation_methods=None,
        ingredient_additions=["queijo, carne"],
    )
    assert result.missing_ingredient_additions == []


def test_deterministic_rejection_explains_what_is_missing_in_portuguese():
    state = {"recipe": recipe(["batata"]), "ingredient_additions": ["queijo"]}

    evaluation = subchef_node(state)["subchef_evaluation"]

    assert evaluation.decision == "rejected"
    assert "queijo" in evaluation.critique
    assert "Impasse" in evaluation.critique


# --- Falha no meio de uma decisão --------------------------------------------------


def chef_failing_on(call_number, monkeypatch):
    calls = {"chef": 0}

    def chef(state):
        calls["chef"] += 1
        if calls["chef"] == call_number:
            raise RuntimeError("falha simulada do provedor")
        return fakes.fake_chef(state)

    monkeypatch.setattr(graph_module, "chef_node", chef)
    monkeypatch.setattr(graph_module, "subchef_node", fakes.fake_subchef)
    return calls


@pytest.mark.parametrize("action", ["accept", "resume", "cancel"])
def test_new_decision_after_a_failed_resume_is_accepted(monkeypatch, action):
    chef_failing_on(3, monkeypatch)
    session = RecipeSession()
    session.start(create_initial_state("coxinha", "t1"))
    session.submit_impasse_decision(
        "t1", decision("save", 0, "s1", ingredient_additions="queijo, carne")
    )
    with pytest.raises(RuntimeError):
        session.submit_impasse_decision("t1", decision("resume", 1, "r1"))

    state = session.get_state("t1")
    assert session.is_recoverable("t1")

    result = session.submit_impasse_decision(
        "t1", decision(action, state["state_version"], f"{action}-2")
    )

    assert result["status"] in ("completed", "cancelled")
    assert result.get("last_error") is None


def test_recover_returns_the_conversation_to_the_impasse(monkeypatch):
    chef_failing_on(3, monkeypatch)
    session = RecipeSession()
    session.start(create_initial_state("coxinha", "t1"))
    session.submit_impasse_decision(
        "t1", decision("save", 0, "s1", ingredient_additions=["queijo"])
    )
    with pytest.raises(RuntimeError):
        session.submit_impasse_decision("t1", decision("resume", 1, "r1"))

    recovered = session.recover("t1")

    assert recovered["status"] == "awaiting_user"
    assert recovered["last_error"] == RECOVERY_MESSAGE
    assert not session.is_recoverable("t1")


def always_reject(monkeypatch):
    monkeypatch.setattr(graph_module, "chef_node", fakes.fake_chef)
    monkeypatch.setattr(
        graph_module,
        "subchef_node",
        lambda state: {
            "subchef_evaluation": SubChefEvaluation(decision="rejected", critique="Ainda não.")
        },
    )


def test_resume_has_a_limit_but_accept_still_works(monkeypatch):
    always_reject(monkeypatch)
    session = RecipeSession()
    state = session.start(create_initial_state("coxinha", "t1"))

    for cycle in range(3):
        state = session.submit_impasse_decision(
            "t1", decision("resume", state["state_version"], f"r{cycle}")
        )
        assert state["status"] == "awaiting_user"

    with pytest.raises(ResumeLimitReached):
        session.submit_impasse_decision("t1", decision("resume", state["state_version"], "r-final"))

    accepted = session.submit_impasse_decision(
        "t1", decision("accept", state["state_version"], "accept-1")
    )
    assert accepted["status"] == "completed"


# --- API -------------------------------------------------------------------------


class InlineExecutor:
    def submit(self, job):
        job()

    def shutdown(self, wait=True, cancel_futures=False):
        pass


def client_for(tmp_path):
    app = create_app(RecipeSession(), image_dir=tmp_path, cors_origins=[], executor=InlineExecutor())
    return TestClient(app)


def post_decision(client, thread_id, action, version, key, **extra):
    body = {"action": action, "expected_state_version": version, "idempotency_key": key, **extra}
    return client.post(f"/recipes/{thread_id}/impasse", json=body)


def test_api_shows_the_impasse_again_after_a_failed_resume(monkeypatch, tmp_path):
    chef_failing_on(3, monkeypatch)
    with client_for(tmp_path) as client:
        thread_id = client.post("/recipes", json={"raw_input": "coxinha"}).json()["thread_id"]
        post_decision(client, thread_id, "save", 0, "s1", ingredient_additions=["queijo, carne"])
        assert post_decision(client, thread_id, "resume", 1, "r1").status_code == 202

        state = client.get(f"/recipes/{thread_id}").json()
        assert state["status"] == "awaiting_user"
        assert state["critique"].startswith(RECOVERY_MESSAGE)
        assert "falha simulada" in state["error"]
        assert state["ingredient_additions"] == ["queijo", "carne"]

        accepted = post_decision(client, thread_id, "accept", state["state_version"], "a1")
        assert accepted.status_code == 202
        assert client.get(f"/recipes/{thread_id}").json()["status"] == "completed"


def test_api_refuses_resume_after_the_limit(monkeypatch, tmp_path):
    always_reject(monkeypatch)
    with client_for(tmp_path) as client:
        thread_id = client.post("/recipes", json={"raw_input": "coxinha"}).json()["thread_id"]
        for cycle in range(3):
            version = client.get(f"/recipes/{thread_id}").json()["state_version"]
            post_decision(client, thread_id, "resume", version, f"r{cycle}")

        state = client.get(f"/recipes/{thread_id}").json()
        assert state["resume_allowed"] is False

        refused = post_decision(client, thread_id, "resume", state["state_version"], "r-final")
        assert refused.status_code == 409
        assert refused.json()["detail"]["code"] == "resume_limit_reached"


def test_api_exposes_the_rejection_evidence(monkeypatch, tmp_path):
    def chef_ignoring_additions(state):
        result = fakes.fake_chef({**state, "ingredient_additions": []})
        return result

    def subchef(state):
        # Sem adições, rejeita sem LLM; com adições, usa o SubChef real, cuja
        # checagem determinística responde antes de chamar o modelo.
        if not state.get("ingredient_additions"):
            return fakes.fake_subchef(state)
        return subchef_node(state)

    monkeypatch.setattr(graph_module, "chef_node", chef_ignoring_additions)
    monkeypatch.setattr(graph_module, "subchef_node", subchef)
    with client_for(tmp_path) as client:
        thread_id = client.post("/recipes", json={"raw_input": "coxinha"}).json()["thread_id"]
        post_decision(client, thread_id, "save", 0, "s1", ingredient_additions="queijo e cebola")
        post_decision(client, thread_id, "resume", 1, "r1")
        state = client.get(f"/recipes/{thread_id}").json()

    assert state["status"] == "awaiting_user"
    assert state["ingredient_additions"] == ["queijo", "cebola"]
    assert state["evidence"] == [
        "Itens adicionados no Impasse que a receita ainda não usa: queijo, cebola."
    ]
    assert "queijo, cebola" in state["critique"]


def test_accepting_a_proposal_that_ignores_saved_items_completes(monkeypatch):
    """Aceitar como está não pode falhar por itens salvos que a proposta não usa."""
    always_reject(monkeypatch)
    session = RecipeSession()
    session.start(create_initial_state("coxinha", "t1"))
    session.submit_impasse_decision(
        "t1", decision("save", 0, "s1", ingredient_additions=["trufa"])
    )

    accepted = session.submit_impasse_decision("t1", decision("accept", 1, "a1"))

    assert accepted["status"] == "completed"
    assert accepted["final_response"]["resource_validation"] == "incomplete"
