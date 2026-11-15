from src.state import criar_estado_inicial


def test_estado_inicial_preserva_entrada_e_define_controles():
    pedido = "Quero uma coxinha de batata com frango."
    estado = criar_estado_inicial(pedido, "conversa-1")

    assert estado["raw_input"] == pedido
    assert estado["thread_id"] == "conversa-1"

    assert len(estado["messages"]) == 1
    assert estado["messages"][0].content == pedido
    assert estado["messages"][0].type == "human"

    assert estado["version"] == 0
    assert estado["revision_count"] == 0
    assert estado["total_attempts"] == 0
    assert estado["max_revisions"] == 2
    assert estado["status"] == "in_revision"

    assert estado["state_version"] == 0
    assert estado["state_schema_version"] == 1


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