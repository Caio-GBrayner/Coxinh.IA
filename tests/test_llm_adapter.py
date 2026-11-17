from unittest.mock import Mock
from src import config

import pytest
from pydantic import SecretStr

from src.config import LLMConfig
from src.utils import llm_adapter


@pytest.mark.parametrize("temperature", [0.1, 0.7])
def test_cria_llm_com_configuracao(monkeypatch, temperature):
    """Verifica se o adaptador repassa a chave, o modelo e a temperatura e retorna o cliente criado."""
    config_teste = LLMConfig(
        LLM_KEY=SecretStr("chave-de-teste"),
        LLM_MODEL="modelo-de-teste",
    )

    monkeypatch.setattr(
        llm_adapter,
        "load_llm_config",
        lambda: config_teste,
    )

    chat_groq_simulado = Mock()
    monkeypatch.setattr(llm_adapter, "ChatGroq", chat_groq_simulado)

    resultado = llm_adapter.call_llm(temperature=temperature)

    chat_groq_simulado.assert_called_once_with(
        api_key="chave-de-teste",
        model="modelo-de-teste",
        temperature=temperature,
    )

    assert resultado is chat_groq_simulado.return_value

def test_nao_cria_llm_com_configuracao_invalida(monkeypatch):
    """Verifica que a ausência de LLM_KEY impede a criação do cliente LLM."""
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.delenv("LLM_KEY", raising=False)
    monkeypatch.setenv("LLM_MODEL", "modelo-de-teste")

    chat_groq_simulado = Mock()
    monkeypatch.setattr(llm_adapter, "ChatGroq", chat_groq_simulado)

    with pytest.raises(ValueError, match="LLM_KEY"):
        llm_adapter.call_llm(temperature=0.1)

    chat_groq_simulado.assert_not_called()