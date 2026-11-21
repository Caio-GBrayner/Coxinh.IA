import pytest

from src.graph.finalize import finalize_node
from src.schemas import Recipe
from src.state import RecipeState, create_initial_state


@pytest.fixture
def cooked_state() -> RecipeState:
    """Monta o estado de uma receita aprovada após a execução do Cozinheiro."""
    state = create_initial_state("Coxinha de abóbora", "finalize-test")
    state["status"] = "approved"
    state["recipe"] = Recipe(
        dough="Massa de abóbora",
        filling="Abóbora temperada",
        ingredients=["abóbora"],
        preparation="Modele a massa e asse no forno.",
        utensils=["assadeira"],
        preparation_methods=["forno"],
    )
    state["cook_output"] = {
        "title": "Abóboríssima",
        "subtitle": "Coxinha de abóbora",
        "steps": ["Modele a massa.", "Asse no forno."],
        "image_prompt": "Uma coxinha dourada com recheio de abóbora.",
        "ingredients": ["abóbora"],
        "utensils": ["assadeira"],
        "preparation_methods": ["forno"],
    }
    state["cook_resource_validation"] = "incomplete"
    return state


def test_finalize_completes_recipe_before_health_stage(cooked_state):
    """Conclui a receita enquanto o aviso de saúde ainda está pendente."""
    result = finalize_node(cooked_state)
    response = result["final_response"]

    assert result["status"] == "completed"
    assert response["recipe"]["title"] == "Abóboríssima"
    assert response["recipe"]["subtitle"] == "Coxinha de abóbora"
    assert response["recipe"]["ingredients"] == ["abóbora"]
    assert response["recipe"]["steps"] == ["Modele a massa.", "Asse no forno."]
    assert response["health"]["health_status"] == "pending"
    assert response["health"]["warning"] is None
    assert response["resource_validation"] == "incomplete"


def test_finalize_keeps_health_separate_from_recipe(cooked_state):
    """Inclui o aviso e suas fontes em uma seção separada da receita."""
    recipe_before = finalize_node(cooked_state)["final_response"]["recipe"]
    source = {"title": "Fonte simulada", "url": "https://example.com/health"}
    cooked_state["health_warning"] = "Aviso informativo de teste."
    cooked_state["health_sources"] = [source]
    cooked_state["health_status"] = "ok"

    response = finalize_node(cooked_state)["final_response"]

    assert response["recipe"] == recipe_before
    assert response["health"]["warning"] == "Aviso informativo de teste."
    assert response["health"]["sources"] == [source]
    assert response["health"]["health_status"] == "ok"


def test_finalize_requires_cook_output(cooked_state):
    """Impede que uma proposta aprovada seja concluída antes do Cozinheiro."""
    del cooked_state["cook_output"]

    with pytest.raises(ValueError, match="exige a saída do Cozinheiro"):
        finalize_node(cooked_state)