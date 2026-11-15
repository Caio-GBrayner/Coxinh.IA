import pytest
from pydantic import ValidationError

from src.schemas import AvaliacaoSubchef, Receita


def test_rejeicao_sem_critica_gera_erro():
    with pytest.raises(ValidationError, match="precisa de uma crítica"):
        AvaliacaoSubchef(
            decision="rejected",
            critique="",
        )


def test_rejeicao_com_critica_e_valida():
    avaliacao = AvaliacaoSubchef(
        decision="rejected",
        critique="O preparo usa um ingrediente não autorizado.",
    )

    assert avaliacao.decision == "rejected"
    assert avaliacao.critique == "O preparo usa um ingrediente não autorizado."


def dados_receita_valida():
    return {
        "massa": "  Massa de batata  ",
        "recheio": "Frango",
        "ingredientes": [" batata ", " frango "],
        "modo_de_preparo": "Modele a massa e acrescente o recheio.",
    }


def test_receita_valida_normaliza_textos():
    receita = Receita(**dados_receita_valida())

    assert receita.massa == "Massa de batata"
    assert receita.ingredientes == ["batata", "frango"]
    assert receita.resumo_da_revisao is None


@pytest.mark.parametrize(
    "campo",
    ["massa", "recheio", "ingredientes", "modo_de_preparo"],
)
def test_receita_exige_campos_obrigatorios(campo):
    dados = dados_receita_valida()
    del dados[campo]

    with pytest.raises(ValidationError) as erro:
        Receita(**dados)

    detalhe = erro.value.errors()[0]
    assert detalhe["loc"] == (campo,)
    assert detalhe["type"] == "missing"


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("massa", ""),
        ("massa", "   "),
        ("recheio", ""),
        ("recheio", "   "),
        ("modo_de_preparo", ""),
        ("modo_de_preparo", "   "),
        ("ingredientes", []),
        ("ingredientes", [""]),
        ("ingredientes", ["batata", "   "]),
        ("massa", 123),
        ("ingredientes", "batata"),
        ("ingredientes", [123]),
    ],
)
def test_receita_rejeita_dados_invalidos(campo, valor):
    dados = dados_receita_valida()
    dados[campo] = valor

    with pytest.raises(ValidationError) as erro:
        Receita(**dados)

    assert erro.value.errors()[0]["loc"][0] == campo


def test_aprovacao_aceita_critica_vazia():
    avaliacao = AvaliacaoSubchef(
        decision="approved",
        critique="",
    )

    assert avaliacao.decision == "approved"
    assert avaliacao.critique == ""


@pytest.mark.parametrize("critica", ["   ", "\n\t"])
def test_rejeicao_nao_aceita_critica_so_com_espacos(critica):
    with pytest.raises(ValidationError, match="precisa de uma crítica"):
        AvaliacaoSubchef(
            decision="rejected",
            critique=critica,
        )


def test_avaliacao_rejeita_decisao_desconhecida():
    with pytest.raises(ValidationError) as erro:
        AvaliacaoSubchef(
            decision="talvez",
            critique="Ainda estou avaliando.",
        )

    assert erro.value.errors()[0]["loc"] == ("decision",)