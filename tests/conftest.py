
import json
from unittest.mock import Mock

import pytest
from langchain_core.runnables import RunnableLambda

from src.graph.nodes import cook


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