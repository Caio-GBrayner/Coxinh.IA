from unittest.mock import Mock

from langchain_core.runnables import RunnableLambda

from src.graph.builder import graph
from src.graph.nodes import chef, subchef
from src.schemas import Recipe, SubChefEvaluation
from src.state import create_initial_state
import pytest


def mock_llm_response(monkeypatch, node_module, *responses):
    """Configura as respostas simuladas do modelo na ordem em que serão usadas."""
    pending_responses = iter(responses)

    def respond(_prompt):
        """Devolve a próxima resposta simulada."""
        return next(pending_responses)

    model = Mock()
    model.with_structured_output.return_value = RunnableLambda(respond)
    mocked_call_llm = Mock(return_value=model)
    monkeypatch.setattr(node_module, "call_llm", mocked_call_llm)
    return mocked_call_llm


def test_graph_approves_on_first_review(monkeypatch):
    """Verifica que a primeira aprovação encerra o fluxo com uma avaliação."""
    recipe = Recipe(
        dough="Massa de batata",
        filling="Frango",
        ingredients=["batata", "frango"],
        preparation="Modele a massa e adicione o recheio.",
        utensils=["panela"],
        preparation_methods=["cozimento"],
    )
    evaluation = SubChefEvaluation(decision="approved", critique="")

    chef_llm = mock_llm_response(monkeypatch, chef, recipe)
    subchef_llm = mock_llm_response(monkeypatch, subchef, evaluation)

    state = create_initial_state("Quero uma coxinha de batata e frango.", "test-approval")
    state["authorized_ingredients"] = recipe.ingredients
    state["authorized_utensils"] = recipe.utensils
    state["authorized_preparation_methods"] = recipe.preparation_methods

    result = graph.invoke(state)

    assert result["status"] == "approved"
    assert result["recipe"] == recipe
    assert result["recipe_version"] == 1
    assert result["revision_count"] == 1
    assert result["total_attempts"] == 1
    chef_llm.assert_called_once()
    subchef_llm.assert_called_once()



@pytest.mark.parametrize(
    ("second_decision", "expected_status"),
    [
        ("approved", "approved"),
        ("rejected", "awaiting_user"),
    ],
)
def test_graph_stops_after_second_review(
    monkeypatch, second_decision, expected_status
):
    """Verifica a volta ao Chef e o encerramento após a segunda avaliação."""
    first_recipe = Recipe(
        dough="Massa de batata",
        filling="Frango",
        ingredients=["batata", "frango"],
        preparation="Modele a coxinha.",
        utensils=["panela"],
        preparation_methods=["cozimento"],
    )
    revised_recipe = first_recipe.model_copy(
        update={"preparation": "Cozinhe a batata, modele a massa e adicione o recheio."}
    )
    first_review = SubChefEvaluation(
        decision="rejected",
        critique="Detalhe como preparar a massa.",
    )
    second_review = SubChefEvaluation(
        decision=second_decision,
        critique="Detalhe o tempo de cozimento." if second_decision == "rejected" else "",
    )

    chef_llm = mock_llm_response(monkeypatch, chef, first_recipe, revised_recipe)
    subchef_llm = mock_llm_response(monkeypatch, subchef, first_review, second_review)

    state = create_initial_state("Quero uma coxinha de batata e frango.", "test-retry")
    result = graph.invoke(state)

    assert result["status"] == expected_status
    assert result["recipe"] == revised_recipe
    assert result["subchef_evaluation"].decision == second_decision
    assert result["recipe_version"] == 2
    assert result["revision_count"] == 2
    assert result["total_attempts"] == 2
    assert chef_llm.call_count == 2
    assert subchef_llm.call_count == 2