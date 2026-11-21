import json
from unittest.mock import Mock

import pytest
from langchain_core.runnables import RunnableLambda

from src.graph.nodes import cook
from src.schemas import CookOutput, Recipe
from src.state import RecipeState, create_initial_state


@pytest.fixture
def approved_state() -> RecipeState:
    """Cria uma proposta aprovada com forno como método de preparo."""
    state = create_initial_state("Coxinha de abóbora", "cook-test")
    state["status"] = "approved"
    state["recipe"] = Recipe(
        dough="Massa de abóbora",
        filling="Abóbora temperada",
        ingredients=["abóbora"],
        preparation="Modele a massa e asse no forno.",
        utensils=["assadeira"],
        preparation_methods=["forno"],
    )
    return state


@pytest.fixture
def valid_output() -> CookOutput:
    """Cria uma saída que preserva os recursos da proposta."""
    return CookOutput(
        title="Abóboríssima",
        subtitle="Coxinha de abóbora",
        steps=["Modele a massa.", "Asse no forno."],
        image_prompt="Uma coxinha dourada com recheio de abóbora.",
        ingredients=["abóbora"],
        utensils=["assadeira"],
        preparation_methods=["forno"],
    )


def stub_cook_model(monkeypatch, *outputs: CookOutput) -> list[dict]:
    """Simula o modelo e registra o contexto enviado em cada tentativa."""
    responses = iter(outputs)
    contexts = []

    def respond(prompt):
        """Lê o contexto da mensagem e devolve a próxima resposta simulada."""
        message = prompt.to_messages()[-1]
        contexts.append(json.loads(message.content))
        return next(responses)

    model = Mock()
    model.with_structured_output.return_value = RunnableLambda(respond)
    monkeypatch.setattr(cook, "call_llm", Mock(return_value=model))
    return contexts


def test_cook_accepts_output_that_preserves_approved_resources(
    monkeypatch, approved_state, valid_output
):
    """Aceita recursos fiéis à proposta e sinaliza autorizações ausentes."""
    contexts = stub_cook_model(monkeypatch, valid_output)

    result = cook.cook_node(approved_state)

    assert len(contexts) == 1
    assert result["cook_output"] == valid_output.model_dump(mode="json")
    assert result["recipe_steps"] == "1. Modele a massa.\n2. Asse no forno."
    assert result["image_prompt"] == valid_output.image_prompt
    assert result["cook_resource_validation"] == "incomplete"
    assert approved_state["recipe"].preparation_methods == ["forno"]


def test_cook_retries_once_after_an_unapproved_substitution(
    monkeypatch, approved_state, valid_output
):
    """Pede uma correção quando o modelo troca o método aprovado."""
    invalid_output = valid_output.model_copy(
        update={"preparation_methods": ["air fryer"]}
    )
    contexts = stub_cook_model(monkeypatch, invalid_output, valid_output)

    result = cook.cook_node(approved_state)

    assert len(contexts) == 2
    assert "resource_correction" not in contexts[0]
    assert "preparation_methods" in contexts[1]["resource_correction"]
    assert result["cook_output"]["preparation_methods"] == ["forno"]


def test_cook_raises_when_both_attempts_diverge(
    monkeypatch, approved_state, valid_output
):
    """Encerra com erro de finalização após duas saídas divergentes."""
    invalid_output = valid_output.model_copy(
        update={"preparation_methods": ["air fryer"]}
    )
    contexts = stub_cook_model(monkeypatch, invalid_output, invalid_output)

    with pytest.raises(ValueError, match="Falha na finalização"):
        cook.cook_node(approved_state)

    assert len(contexts) == 2