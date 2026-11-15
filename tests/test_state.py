import pytest

from src.state import criar_estado_inicial


def test_estado_inicial_preserva_entrada_e_define_controles():
    pedido = "Quero uma coxinha de batata com frango."
    estado = criar_estado_inicial(pedido, "conversa-1")

    assert estado["raw_input"] == pedido
    assert estado["thread_id"] == "conversa-1"

    assert len(estado["messages"]) == 1
    assert estado["messages"][0].content == pedido
    assert estado["messages"][0].type == "human"

    assert estado["recipe_version"] == 0
    assert estado["revision_count"] == 0
    assert estado["total_attempts"] == 0
    assert estado["max_revisions"] == 2
    assert estado["status"] == "in_revision"

    assert estado["state_version"] == 0
    assert estado["state_schema_version"] == 1
    assert estado["ingredientes_autorizados"] is None
    assert estado["utensilios_autorizados"] is None
    assert estado["meios_preparo_autorizados"] is None


def test_limite_de_revisoes_pode_ser_configurado():
    estado = criar_estado_inicial(
        "Pedido",
        "conversa-1",
        max_revisions=3,
    )

    assert estado["max_revisions"] == 3


@pytest.mark.parametrize("max_revisions", [0, -1, True])
def test_limite_de_revisoes_invalido_e_rejeitado(max_revisions):
    with pytest.raises(ValueError, match="positive integer"):
        criar_estado_inicial("Pedido", "conversa-1", max_revisions=max_revisions)


def test_conversas_nao_compartilham_listas_e_dicionarios():
    primeiro = criar_estado_inicial("Pedido A", "conversa-1")
    segundo = criar_estado_inicial("Pedido B", "conversa-2")

    primeiro["ingredient_additions"].append("queijo")
    primeiro["user_preferences"]["tom"] = "divertido"
    primeiro["messages"].clear()

    assert segundo["ingredient_additions"] == []
    assert segundo["user_preferences"] == {}
    assert len(segundo["messages"]) == 1
    assert segundo["messages"][0].content == "Pedido B"