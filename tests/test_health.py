from unittest.mock import Mock

from langchain_core.runnables import RunnableLambda
import pydantic
import pytest

from src.graph.nodes import health
from src.graph.nodes.health import HealthAdvice, HealthSource, health_node
from src.schemas import Recipe
from src.state import create_initial_state


def create_recipe():
    return Recipe(
        dough="Potato dough",
        filling="Chicken",
        ingredients=["potato", "chicken"],
        preparation="Boil the potatoes and shape the dough.",
        utensils=["pot"],
        preparation_methods=["boiling"],
    )


def create_advice(**overrides):
    values = {
        "health_warning": "Aviso culinário não oficial: consumo com moderação.",
        "contraindications": ["Pessoas com alergia a frango."],
        "possible_effects": [],
        "sources_used": [
            {"title": "Fonte A", "url": "https://example.test/a"},
        ],
        "uncertainty": "Confiança alta nas fontes consultadas.",
    }
    values.update(overrides)
    return HealthAdvice(**values)


def retrieved_item(title="Fonte A", url="https://example.test/a"):
    return {"title": title, "url": url, "content": "trecho"}


def mock_structured_model(monkeypatch, output, *, error=None):
    messages = []

    def invoke(prompt_value):
        messages.extend(prompt_value.to_messages())
        if error is not None:
            raise error
        return output

    structured_model = RunnableLambda(invoke)
    chat_model = Mock()
    chat_model.with_structured_output.return_value = structured_model
    mocked_call_llm = Mock(return_value=chat_model)
    monkeypatch.setattr(health, "call_llm", mocked_call_llm)
    return chat_model, mocked_call_llm, messages


def mock_search(monkeypatch, results_by_query=None):
    queries = []
    results_by_query = results_by_query or {}

    def search(query):
        queries.append(query)
        return list(results_by_query.get(query, []))

    monkeypatch.setattr(health, "HEALTH_SEARCH", search)
    return queries


def create_state():
    state = create_initial_state("Make a coxinha.", "conversation-1")
    state["recipe"] = create_recipe()
    return state


def test_health_returns_only_health_keys_and_keeps_recipe(monkeypatch):
    state = create_state()
    original_recipe = state["recipe"]
    mock_search(monkeypatch, {"Potato dough": [retrieved_item()]})
    mock_structured_model(monkeypatch, create_advice())

    result = health_node(state)

    assert set(result) == {
        "health_status",
        "health_warning",
        "contraindications",
        "health_sources",
        "health_uncertainty",
    }
    assert result["health_status"] == "ok"
    assert state["recipe"] == original_recipe


def test_health_runs_three_queries_for_dough_filling_and_preparation(monkeypatch):
    state = create_state()
    queries = mock_search(monkeypatch)
    mock_structured_model(monkeypatch, create_advice(sources_used=[], uncertainty="Sem fontes."))

    health_node(state)

    assert queries == [
        "Potato dough",
        "Chicken",
        "Boil the potatoes and shape the dough.",
    ]


def test_health_uses_default_simulated_search_without_network(monkeypatch):
    state = create_state()
    monkeypatch.setattr(health, "HEALTH_SEARCH", health.simulated_health_search)
    mock_structured_model(monkeypatch, create_advice(sources_used=[], uncertainty="Sem fontes."))

    result = health_node(state)

    assert result["health_status"] == "ok"
    assert result["health_sources"] == []


def test_health_calls_model_with_fixed_temperature_and_schema(monkeypatch):
    state = create_state()
    mock_search(monkeypatch)
    chat_model, mocked_call_llm, _ = mock_structured_model(
        monkeypatch, create_advice()
    )

    health_node(state)

    mocked_call_llm.assert_called_once_with(health.HEALTH_TEMPERATURE)
    chat_model.with_structured_output.assert_called_once_with(HealthAdvice)


def test_health_input_excludes_original_request(monkeypatch):
    state = create_initial_state("SECRET_REQUEST_TEXT", "conversation-1")
    state["recipe"] = create_recipe()
    mock_search(monkeypatch, {"Potato dough": [retrieved_item()]})
    _, _, messages = mock_structured_model(monkeypatch, create_advice())

    health_node(state)

    assert "SECRET_REQUEST_TEXT" not in messages[1].content


def test_health_drops_source_not_present_in_retrieved_context(monkeypatch):
    state = create_state()
    mock_search(monkeypatch, {"Potato dough": [retrieved_item()]})
    fabricated = {"title": "Fonte inventada", "url": "https://invented.test/x"}
    mock_structured_model(
        monkeypatch,
        create_advice(sources_used=[fabricated]),
    )

    result = health_node(state)

    assert result["health_sources"] == []
    assert result["health_status"] == "ok"


def test_health_without_sources_is_ok_with_uncertainty(monkeypatch):
    state = create_state()
    mock_search(monkeypatch)
    mock_structured_model(
        monkeypatch,
        create_advice(sources_used=[], uncertainty="Nenhuma fonte relevante."),
    )

    result = health_node(state)

    assert result["health_status"] == "ok"
    assert result["health_sources"] == []
    assert result["health_uncertainty"]


def test_health_model_failure_is_unavailable_and_keeps_recipe(monkeypatch):
    state = create_state()
    original_recipe = state["recipe"]
    mock_search(monkeypatch)
    mock_structured_model(monkeypatch, None, error=RuntimeError("boom"))

    result = health_node(state)

    assert result["health_status"] == "unavailable"
    assert result["health_warning"] is None
    assert result["health_uncertainty"] == health.UNAVAILABLE_MESSAGE
    assert state["recipe"] == original_recipe


def test_health_search_failure_is_unavailable(monkeypatch):
    state = create_state()

    def failing_search(query):
        raise ConnectionError("search down")

    monkeypatch.setattr(health, "HEALTH_SEARCH", failing_search)
    mocked_call_llm = Mock()
    monkeypatch.setattr(health, "call_llm", mocked_call_llm)

    result = health_node(state)

    assert result["health_status"] == "unavailable"
    mocked_call_llm.assert_not_called()


def test_health_requires_a_recipe():
    state = create_initial_state("Make a coxinha.", "conversation-1")

    with pytest.raises(ValueError, match="requires a recipe"):
        health_node(state)


def test_advice_accepts_empty_contraindications_when_unsupported():
    advice = create_advice(
        contraindications=[],
        uncertainty="Nenhuma contraindicação sustentada pelas fontes.",
    )

    assert advice.contraindications == []


def test_health_passes_empty_contraindications_through(monkeypatch):
    state = create_state()
    mock_search(monkeypatch, {"Potato dough": [retrieved_item()]})
    mock_structured_model(
        monkeypatch,
        create_advice(
            contraindications=[],
            uncertainty="Nenhuma contraindicação sustentada pelas fontes.",
        ),
    )

    result = health_node(state)

    assert result["contraindications"] == []
    assert result["health_status"] == "ok"


def test_advice_without_sources_must_declare_uncertainty():
    with pytest.raises(pydantic.ValidationError):
        create_advice(sources_used=[], uncertainty=None)


def test_source_requires_title():
    with pytest.raises(pydantic.ValidationError):
        HealthSource(title="   ")
