import pytest


from src import config


def test_loads_valid_configuration(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_KEY", " test-key ")
    monkeypatch.setenv("LLM_MODEL", " test-model ")

    result = config.load_llm_config()

    assert result.api_key.get_secret_value() == "test-key"
    assert result.model == "test-model"
    assert result.provider == "groq"


def test_loads_google_configuration(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", " google-test-key ")
    monkeypatch.setenv("LLM_MODEL", "gemini-test-model")

    result = config.load_llm_config()

    assert result.api_key.get_secret_value() == "google-test-key"
    assert result.model == "gemini-test-model"
    assert result.provider == "google"


@pytest.mark.parametrize(
    "variable, value",
    [
        ("LLM_KEY", None),
        ("LLM_KEY", ""),
        ("LLM_KEY", "   "),
        ("LLM_MODEL", None),
        ("LLM_MODEL", ""),
        ("LLM_MODEL", "   "),
    ],
)
def test_rejects_invalid_configuration(monkeypatch, variable, value):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    if value is None:
        monkeypatch.delenv(variable, raising=False)
    else:
        monkeypatch.setenv(variable, value)

    with pytest.raises(ValueError, match=variable):
        config.load_llm_config()


def test_rejects_google_configuration_without_google_key(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("LLM_MODEL", "gemini-test-model")

    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        config.load_llm_config()


def test_carrega_configuracao_tavily_valida(monkeypatch):
    """Verifica a leitura da chave do Tavily e a remoção de espaços."""

    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("TAVILY_API_KEY", " chave-de-teste ")

    resultado = config.load_tavily_config()

    assert resultado.api_key.get_secret_value() == "chave-de-teste"


def test_rejeita_configuracao_tavily_sem_chave(monkeypatch):
    """Verifica que a ausência da chave do Tavily gera um erro explícito."""

    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with pytest.raises(ValueError, match="TAVILY_API_KEY must be set"):
        config.load_tavily_config()
