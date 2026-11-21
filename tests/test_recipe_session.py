from src.recipe_session import RecipeSession
from src.state import create_initial_state
from test_checkpoint import create_decision, create_in_memory_workflow


def test_session_saves_recipes_after_start_and_resume(
    monkeypatch, stub_cook_llm
):
    """Salva na mesma galeria as receitas concluídas direto ou após retomada."""
    create_in_memory_workflow(
        monkeypatch,
        ["approved", "rejected", "rejected", "approved"],
    )
    session = RecipeSession()

    first = session.start(
        create_initial_state("Coxinha de frango", "thread-1")
    )

    assert first["status"] == "completed"
    assert [item["id"] for item in session.history.list_recipes()] == [
        "thread-1",
    ]

    second = session.start(
        create_initial_state("Outra coxinha", "thread-2")
    )

    assert second["status"] == "awaiting_user"
    assert session.history.get_recipe("thread-2") is None

    decision = create_decision(
        "resume",
        expected_state_version=0,
        idempotency_key="resume-1",
        ingredient_additions=["mushroom"],
    )
    resumed = session.submit_impasse_decision("thread-2", decision)

    assert resumed["status"] == "completed"
    assert [item["id"] for item in session.history.list_recipes()] == [
        "thread-1",
        "thread-2",
    ]

    saved = session.history.get_recipe("thread-2")
    assert saved is not None
    assert saved["recipe"] == resumed["final_response"]["recipe"]
    assert "mushroom" in saved["recipe"]["ingredients"]
    assert stub_cook_llm.call_count == 2