from src import config
import pytest


def test_carrega_configuracao_valida(monkeypatch):
    """Verifica se a configuração carrega a chave e o modelo, removendo espaços das extremidades."""
    monkeypatch.setattr(config, "load_dotenv", lambda: None)

    monkeypatch.setenv("LLM_KEY", " chave-de-teste ")
    monkeypatch.setenv("LLM_MODEL", " modelo-de-teste ")

    resultado = config.load_llm_config()

    assert resultado.LLM_KEY.get_secret_value() == "chave-de-teste"
    assert resultado.LLM_MODEL == "modelo-de-teste"

@pytest.mark.parametrize(
    "variavel, valor",
    [
        ("LLM_KEY", None),
        ("LLM_KEY", ""),
        ("LLM_KEY", "   "),
        ("LLM_MODEL", None),
        ("LLM_MODEL", ""),
        ("LLM_MODEL", "   "),
    ],
)
def test_rejeita_configuracao_invalida(monkeypatch, variavel, valor):
    """Verifica se variáveis ausentes, vazias ou com apenas espaços geram ValueError identificando o campo inválido."""
    monkeypatch.setattr(config, "load_dotenv", lambda: None)

    monkeypatch.setenv("LLM_KEY", "chave-de-teste")
    monkeypatch.setenv("LLM_MODEL", "modelo-de-teste")

    if valor is None:
        monkeypatch.delenv(variavel, raising=False)
    else:
        monkeypatch.setenv(variavel, valor)

    with pytest.raises(ValueError, match=variavel):
        config.load_llm_config()