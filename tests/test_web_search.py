from unittest.mock import Mock

import pytest
from pydantic import SecretStr

from src.config import TavilyConfig
from src.utils import web_search


@pytest.fixture
def tavily_stub(monkeypatch):
    """Substitui a configuração e o cliente Tavily por objetos simulados."""

    config = TavilyConfig(api_key=SecretStr("chave-de-teste"))
    monkeypatch.setattr(web_search, "load_tavily_config", lambda: config)

    client = Mock()
    client_factory = Mock(return_value=client)
    monkeypatch.setattr(web_search, "TavilyClient", client_factory)

    return client, client_factory


def create_source(**overrides):
    """Cria uma fonte válida e permite alterar campos em cada cenário."""

    source = {
        "title": "Fonte de teste",
        "url": "https://example.org/artigo",
        "content": "Trecho recuperado para o agente.",
    }
    source.update(overrides)
    return source


def test_pesquisa_devolve_fontes_estruturadas(tavily_stub):
    """Verifica os parâmetros enviados e os campos devolvidos ao agente."""

    client, client_factory = tavily_stub
    client.search.return_value = {
        "results": [create_source(score=0.9)]
    }

    resultado = web_search.search_web(" riscos do ingrediente ")

    client_factory.assert_called_once_with(api_key="chave-de-teste")
    client.search.assert_called_once_with(
        query="riscos do ingrediente",
        search_depth="basic",
        max_results=3,
        include_answer=False,
        include_raw_content=False,
        include_images=False,
        auto_parameters=False,
        timeout=20,
    )

    assert resultado == [create_source()]


def test_rejeita_consulta_vazia(tavily_stub):
    """Verifica que uma consulta vazia é rejeitada antes de criar o cliente."""

    _, client_factory = tavily_stub

    with pytest.raises(ValueError, match="precisa estar preenchida"):
        web_search.search_web("   ")

    client_factory.assert_not_called()


def test_pesquisa_sem_resultados_devolve_lista_vazia(tavily_stub):
    """Verifica o retorno de uma pesquisa bem-sucedida sem fontes."""

    client, _ = tavily_stub
    client.search.return_value = {"results": []}

    assert web_search.search_web("consulta de teste") == []


@pytest.mark.parametrize(
    "erro",
    [
        TimeoutError("Tempo esgotado."),
        ConnectionError("Falha de conexão."),
        RuntimeError("Serviço indisponível."),
    ],
)
def test_falha_da_pesquisa_propaga_excecao(tavily_stub, erro):
    """Verifica que falhas técnicas chegam ao chamador como exceções."""

    client, _ = tavily_stub
    client.search.side_effect = erro

    with pytest.raises(type(erro)) as captured:
        web_search.search_web("consulta de teste")

    assert captured.value is erro


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("title", "   "),
        ("url", "endereco-invalido"),
        ("content", ""),
    ],
)
def test_descarta_fonte_invalida(tavily_stub, campo, valor):
    """Verifica o descarte de fontes com campos inválidos."""

    client, _ = tavily_stub
    source = create_source()
    source[campo] = valor
    client.search.return_value = {"results": [source]}

    assert web_search.search_web("consulta de teste") == []


def test_descarta_fonte_sem_url_e_preserva_fonte_valida(tavily_stub):
    """Verifica que uma fonte sem URL não elimina outras fontes válidas."""

    client, _ = tavily_stub
    invalid_source = create_source()
    invalid_source.pop("url")
    valid_source = create_source()

    client.search.return_value = {
        "results": [invalid_source, valid_source]
    }

    assert web_search.search_web("consulta de teste") == [valid_source]


def test_limpa_html_entidades_e_espacos(tavily_stub):
    """Verifica a limpeza do trecho entregue ao agente."""

    client, _ = tavily_stub
    client.search.return_value = {
        "results": [
            create_source(
                content="<p>Risco &amp; cuidado.</p>\n   Consulte a fonte."
            )
        ]
    }

    resultado = web_search.search_web("consulta de teste")

    assert resultado[0]["content"] == "Risco & cuidado. Consulte a fonte."


def test_descarta_trecho_vazio_apos_limpeza(tavily_stub):
    """Verifica o descarte de um trecho que contém apenas marcação HTML."""

    client, _ = tavily_stub
    client.search.return_value = {
        "results": [create_source(content="<p></p>")]
    }

    assert web_search.search_web("consulta de teste") == []


def test_limita_trecho_a_quinhentos_caracteres(tavily_stub):
    """Verifica o tamanho máximo do conteúdo enviado ao agente."""

    client, _ = tavily_stub
    client.search.return_value = {
        "results": [create_source(content="a" * 700)]
    }

    resultado = web_search.search_web("consulta de teste")

    assert resultado[0]["content"] == "a" * 500


def test_limita_retorno_a_tres_fontes(tavily_stub):
    """Verifica o limite mesmo quando o cliente devolve fontes extras."""

    client, _ = tavily_stub
    sources = [
        create_source(url=f"https://example.org/artigo-{index}")
        for index in range(5)
    ]
    client.search.return_value = {"results": sources}

    resultado = web_search.search_web("consulta de teste")

    assert resultado == sources[:3]


def test_chave_ausente_impede_criacao_do_cliente(monkeypatch):
    """Verifica que a falha de configuração acontece antes de criar o cliente."""

    config_loader = Mock(
        side_effect=ValueError("TAVILY_API_KEY must be set.")
    )
    client_factory = Mock()

    monkeypatch.setattr(web_search, "load_tavily_config", config_loader)
    monkeypatch.setattr(web_search, "TavilyClient", client_factory)

    with pytest.raises(ValueError, match="TAVILY_API_KEY must be set"):
        web_search.search_web("consulta de teste")

    client_factory.assert_not_called()