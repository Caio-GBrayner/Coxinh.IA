
import json
from unittest.mock import Mock

import pytest
from langchain_core.runnables import RunnableLambda

from src import mcp_client
from src.graph.nodes import cook, health


@pytest.fixture(autouse=True)
def isolate_tool_client():
    """Dá a cada teste um servidor MCP novo, para o índice de imagens não vazar."""
    mcp_client.reset_default_client()
    yield
    mcp_client.reset_default_client()


@pytest.fixture(autouse=True)
def stub_health_llm(monkeypatch):
    """Impede chamadas reais no nó de saúde. Testes podem sobrescrever o stub."""
    advice = {
        "health_warning": "Aviso culinário não oficial.",
        "contraindications": [],
        "sources_used": [],
        "uncertainty": "Sem fontes simuladas; confiança nenhuma.",
    }
    model = Mock()
    model.with_structured_output.return_value = RunnableLambda(lambda _: advice)
    mocked_call = Mock(return_value=model)
    monkeypatch.setattr(health, "call_llm", mocked_call)
    monkeypatch.setattr(health, "HEALTH_SEARCH", health.simulated_health_search)
    return mocked_call


@pytest.fixture
def stub_cook_llm(monkeypatch):
    """Simula o modelo do Cozinheiro sem chamadas externas."""

    def respond(prompt):
        """Devolve uma apresentação com os recursos da proposta recebida."""
        message = prompt.to_messages()[-1]
        recipe = json.loads(message.content)["recipe"]

        return {
            "title": "Crocância de Frango",
            "subtitle": "Coxinha de frango com massa de batata.",
            "steps": ["Cozinhe as batatas.", "Modele a massa."],
            "image_prompt": "Coxinha dourada com recheio de frango.",
            "ingredients": recipe["ingredients"],
            "utensils": recipe["utensils"],
            "preparation_methods": recipe["preparation_methods"],
        }

    model = Mock()
    model.with_structured_output.return_value = RunnableLambda(respond)
    mocked_call = Mock(return_value=model)
    monkeypatch.setattr(cook, "call_llm", mocked_call)
    return mocked_call