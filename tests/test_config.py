import pytest

from src import config


def test_loads_valid_configuration(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("LLM_KEY", " test-key ")
    monkeypatch.setenv("LLM_MODEL", " test-model ")

    result = config.load_llm_config()

    assert result.api_key.get_secret_value() == "test-key"
    assert result.model == "test-model"


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
    monkeypatch.setenv("LLM_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    if value is None:
        monkeypatch.delenv(variable, raising=False)
    else:
        monkeypatch.setenv(variable, value)

    with pytest.raises(ValueError, match=variable):
        config.load_llm_config()
