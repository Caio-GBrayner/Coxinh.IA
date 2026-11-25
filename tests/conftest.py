
import json
from unittest.mock import Mock

import pytest
from langchain_core.runnables import RunnableLambda

from src import mcp_client
from src.graph import guardrail
from src.graph.nodes import cook, health
from tests.backends import SqliteBackend, postgres_backend


@pytest.fixture(autouse=True)
def isolate_tool_client(monkeypatch):
    """Dá a cada teste um servidor MCP novo, para o índice de imagens não vazar.

    Define MCP_SERVER_URL vazia: sem isso, os testes usariam um servidor
    externo (do .env) com índice próprio, e a imagem voltaria como `reused`.
    Vazia e não removida, porque load_dotenv() recarregaria o valor do .env.
    """
    monkeypatch.setenv("MCP_SERVER_URL", "")
    # Sem chave, o servidor padrão usa o provedor simulado: nenhum teste gera custo.
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    # Nenhum teste envia rastros: sem isso, o .env real ativaria Langfuse e LangSmith.
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    # Os testes nunca gravam no banco do projeto (data/).
    monkeypatch.setenv("PERSISTENCE", "memory")
    monkeypatch.setenv("DATABASE_URL", "")
    mcp_client.reset_default_client()
    yield
    mcp_client.reset_default_client()


@pytest.fixture(params=["sqlite", "postgres"])
def backend(request, tmp_path):
    """Cada banco suportado. O Postgres é pulado sem TEST_DATABASE_URL."""
    if request.param == "sqlite":
        yield SqliteBackend(tmp_path)
        return
    with postgres_backend() as postgres:
        yield postgres


@pytest.fixture(autouse=True)
def stub_judge(monkeypatch):
    """O juiz aprova tudo, sem LLM. Testes do guardrail sobrescrevem o stub."""
    for name in (
        "GUARD_JUDGE_PROVIDER",
        "GUARD_JUDGE_MODEL",
        "GUARD_MAX_INPUT_CHARS",
        "GUARD_JUDGE_TIMEOUT_SECONDS",
    ):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("GUARD_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    judge = Mock(
        return_value=guardrail.JudgeVerdict(verdict="legitima", reason="Receita.")
    )
    monkeypatch.setattr(guardrail, "run_judge", judge)
    return judge


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