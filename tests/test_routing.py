import pytest

from src.graph.routing import registrar_avaliacao_subchef, route_after_subchef
from src.schemas import AvaliacaoSubchef
from src.state import criar_estado_inicial


def estado_com_avaliacao(decision: str, max_revisions: int = 2):
    estado = criar_estado_inicial("Quero uma coxinha criativa.", "thread-1")
    estado["max_revisions"] = max_revisions
    estado["avaliacao"] = AvaliacaoSubchef(
        decision=decision,
        critique="Rever a proposta." if decision == "rejected" else "",
    )
    return estado


def test_aprovacao_encaminha_ao_cozinheiro_e_conta_avaliacao():
    estado = estado_com_avaliacao("approved", max_revisions=1)

    atualizado = registrar_avaliacao_subchef(estado)

    assert atualizado["revision_count"] == 0
    assert atualizado["total_attempts"] == 1
    assert atualizado["status"] == "approved"
    assert route_after_subchef(atualizado) == "cook"


def test_rejeicao_antes_do_limite_volta_ao_chef():
    estado = estado_com_avaliacao("rejected", max_revisions=2)

    atualizado = registrar_avaliacao_subchef(estado)

    assert atualizado["revision_count"] == 1
    assert atualizado["total_attempts"] == 1
    assert atualizado["status"] == "in_revision"
    assert route_after_subchef(atualizado) == "chef"


def test_rejeicao_no_limite_encaminha_ao_impasse():
    estado = estado_com_avaliacao("rejected", max_revisions=1)
    primeira_revisao = registrar_avaliacao_subchef(estado)
    segunda_avaliacao = {
        **primeira_revisao,
        "avaliacao": AvaliacaoSubchef(
            decision="rejected",
            critique="A proposta ainda precisa de ajustes.",
        ),
    }

    atualizado = registrar_avaliacao_subchef(segunda_avaliacao)

    assert atualizado["revision_count"] == 1
    assert atualizado["total_attempts"] == 2
    assert atualizado["status"] == "awaiting_user"
    assert route_after_subchef(atualizado) == "impasse"


def test_duas_revisoes_sao_permitidas_antes_do_impasse():
    estado = estado_com_avaliacao("rejected", max_revisions=2)
    primeira_avaliacao = registrar_avaliacao_subchef(estado)
    segunda_avaliacao = registrar_avaliacao_subchef(primeira_avaliacao)
    terceira_avaliacao = registrar_avaliacao_subchef(segunda_avaliacao)

    assert segunda_avaliacao["revision_count"] == 2
    assert route_after_subchef(segunda_avaliacao) == "chef"
    assert terceira_avaliacao["revision_count"] == 2
    assert terceira_avaliacao["total_attempts"] == 3
    assert route_after_subchef(terceira_avaliacao) == "impasse"


def test_aprovacao_na_ultima_tentativa_ainda_encaminha_ao_cozinheiro():
    estado = estado_com_avaliacao("approved", max_revisions=2)
    estado["revision_count"] = 2
    estado["total_attempts"] = 2

    atualizado = registrar_avaliacao_subchef(estado)

    assert atualizado["revision_count"] == 2
    assert atualizado["total_attempts"] == 3
    assert route_after_subchef(atualizado) == "cook"


def test_falha_sem_avaliacao_nao_consume_tentativa():
    estado = criar_estado_inicial("Pedido", "thread-1")

    with pytest.raises(TypeError, match="valid SubChef evaluation"):
        registrar_avaliacao_subchef(estado)

    assert estado["revision_count"] == 0
    assert estado["total_attempts"] == 0


def test_nao_registra_avaliacao_em_estado_que_nao_esta_em_revisao():
    estado = estado_com_avaliacao("rejected")
    estado["status"] = "awaiting_user"

    with pytest.raises(ValueError, match="workflow is in review"):
        registrar_avaliacao_subchef(estado)

    assert estado["revision_count"] == 0
    assert estado["total_attempts"] == 0


@pytest.mark.parametrize(
    "field, value",
    [
        ("revision_count", -1),
        ("total_attempts", -1),
        ("max_revisions", 0),
        ("max_revisions", -1),
        ("revision_count", 3),
    ],
)
def test_contadores_invalidos_sao_rejeitados(field, value):
    estado = estado_com_avaliacao("rejected")
    estado[field] = value

    with pytest.raises(ValueError):
        registrar_avaliacao_subchef(estado)


def test_estado_original_nao_e_mutado_ao_registrar_avaliacao():
    estado = estado_com_avaliacao("rejected")

    registrar_avaliacao_subchef(estado)

    assert estado["revision_count"] == 0
    assert estado["total_attempts"] == 0
