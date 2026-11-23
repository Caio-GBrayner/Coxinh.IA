from unittest.mock import Mock

import pytest
from pydantic import SecretStr

from src import config
from src.config import LLMConfig
from src.utils import llm_adapter


@pytest.mark.parametrize("temperature", [0.1, 0.7])
def test_creates_chat_model_from_configuration(monkeypatch, temperature):
    test_config = LLMConfig(
        api_key=SecretStr("test-key"),
        model="test-model",
    )
    monkeypatch.setattr(llm_adapter, "load_llm_config", lambda: test_config)
    mocked_chat_model = Mock()
    monkeypatch.setattr(llm_adapter, "ChatGroq", mocked_chat_model)

    result = llm_adapter.call_llm(temperature=temperature)

    mocked_chat_model.assert_called_once_with(
        api_key=SecretStr("test-key"),
        model="test-model",
        temperature=temperature,
    )
    assert result is mocked_chat_model.return_value


def test_does_not_create_chat_model_with_invalid_configuration(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("LLM_KEY", raising=False)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    mocked_chat_model = Mock()
    monkeypatch.setattr(llm_adapter, "ChatGroq", mocked_chat_model)

    with pytest.raises(ValueError, match="LLM_KEY"):
        llm_adapter.call_llm(temperature=0.1)

    mocked_chat_model.assert_not_called()


def test_creates_google_chat_model_from_configuration(monkeypatch):
    test_config = LLMConfig(
        api_key=SecretStr("google-test-key"),
        model="gemini-test-model",
        provider="google",
    )
    monkeypatch.setattr(llm_adapter, "load_llm_config", lambda: test_config)
    mocked_chat_model = Mock()
    monkeypatch.setattr(llm_adapter, "ChatGoogleGenerativeAI", mocked_chat_model)

    result = llm_adapter.call_llm(temperature=0.4)

    mocked_chat_model.assert_called_once_with(
        api_key="google-test-key",
        model="gemini-test-model",
    )
    assert result is mocked_chat_model.return_value
