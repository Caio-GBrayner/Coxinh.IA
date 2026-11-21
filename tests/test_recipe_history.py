import pytest

from src.recipe_history import SessionRecipeHistory


def completed_result(thread_id: str, title: str) -> dict[str, object]:
    """Monta um resultado concluído no formato recebido do grafo."""
    return {
        "thread_id": thread_id,
        "status": "completed",
        "final_response": {
            "recipe": {
                "title": title,
                "ingredients": ["abóbora"],
            },
        },
    }


def test_history_lists_and_opens_recipes_from_same_session():
    """Confere que dois pedidos ficam disponíveis na mesma sessão."""
    history = SessionRecipeHistory()

    first_id = history.save_completed(completed_result("thread-1", "Abóboríssima"))
    second_id = history.save_completed(completed_result("thread-2", "Crocante"))

    assert [item["id"] for item in history.list_recipes()] == [first_id, second_id]

    recipe = history.get_recipe(second_id)
    assert recipe is not None
    assert recipe["recipe"]["title"] == "Crocante"


def test_history_keeps_sessions_separate():
    """Confere que uma sessão não encontra receitas de outra."""
    first_session = SessionRecipeHistory()
    second_session = SessionRecipeHistory()

    recipe_id = first_session.save_completed(
        completed_result("thread-1", "Abóboríssima")
    )

    assert second_session.list_recipes() == []
    assert second_session.get_recipe(recipe_id) is None


def test_history_does_not_duplicate_the_same_execution():
    """Confere que salvar a mesma execução mantém uma única entrada."""
    history = SessionRecipeHistory()
    result = completed_result("thread-1", "Abóboríssima")

    assert history.save_completed(result) == "thread-1"
    assert history.save_completed(result) == "thread-1"
    assert len(history.list_recipes()) == 1


def test_history_protects_saved_recipe_from_changes():
    """Confere que editar a resposta consultada preserva a receita salva."""
    history = SessionRecipeHistory()
    recipe_id = history.save_completed(completed_result("thread-1", "Abóboríssima"))

    recipe = history.get_recipe(recipe_id)
    assert recipe is not None
    recipe["recipe"]["ingredients"].append("cebola")

    saved_recipe = history.get_recipe(recipe_id)
    assert saved_recipe is not None
    assert saved_recipe["recipe"]["ingredients"] == ["abóbora"]


def test_history_rejects_unfinished_execution():
    """Confere que uma receita pausada fica fora da galeria."""
    history = SessionRecipeHistory()

    with pytest.raises(ValueError, match="receitas concluídas"):
        history.save_completed({"thread_id": "thread-1", "status": "awaiting_user"})

    assert history.list_recipes() == []