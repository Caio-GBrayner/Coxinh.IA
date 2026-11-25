from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from src.graph.impasse import ImpasseDecision, StateVersionConflict
from src.persistence.database import persistence_mode
from src.persistence.decision_store import VersionAlreadyClaimed
from src.persistence.factory import build_session
from src.persistence.recipe_store import (
    CorruptedRecipe,
    UnsupportedSchemaVersion,
)
from src.recipe_history import SessionRecipeHistory
from src.schemas import Recipe
from src.state import create_initial_state
from tests.fakes import install_fake_agents


pytestmark = pytest.mark.usefixtures("stub_cook_llm")


# --- Receitas concluídas -------------------------------------------------------


def response(title: str) -> dict[str, object]:
    return {"recipe": {"title": title, "ingredients": ["queijo"]}, "image": {"url": None}}


def test_store_survives_a_new_instance(backend):
    backend.recipes().save("thread-1", response("Queijuda"))

    backend.restart()
    reopened = backend.recipes()

    assert reopened.get("thread-1")["recipe"]["title"] == "Queijuda"
    assert [recipe_id for recipe_id, _ in reopened.list()] == ["thread-1"]


def test_store_lists_in_save_order_and_updates_without_duplicates(backend):
    store = backend.recipes()
    store.save("thread-1", response("Primeira"))
    store.save("thread-2", response("Segunda"))
    store.save("thread-1", response("Primeira revista"))

    listed = store.list()

    assert [recipe_id for recipe_id, _ in listed] == ["thread-1", "thread-2"]
    assert listed[0][1]["recipe"]["title"] == "Primeira revista"
    assert store.get("missing") is None


def test_corrupted_and_future_rows_are_skipped_in_list_and_fail_in_get(backend):
    store = backend.recipes()
    store.save("good", response("Boa"))
    backend.insert_raw_recipe("broken", 1, "{not json")
    backend.insert_raw_recipe("future", 99, "{}")

    assert [recipe_id for recipe_id, _ in store.list()] == ["good"]
    with pytest.raises(CorruptedRecipe):
        store.get("broken")
    with pytest.raises(UnsupportedSchemaVersion):
        store.get("future")


def test_store_accepts_concurrent_writes_from_threads(backend):
    store = backend.recipes()

    def save_many(worker: int) -> None:
        for index in range(15):
            store.save(f"w{worker}-{index}", response(f"{worker}-{index}"))

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(save_many, range(6)))

    assert len(store.list()) == 90


def test_histories_sharing_a_store_see_the_same_recipes(backend):
    store = backend.recipes()
    writer = SessionRecipeHistory(store=store)
    reader = SessionRecipeHistory(store=backend.recipes())

    writer.save_completed(
        {"thread_id": "thread-1", "status": "completed", "final_response": response("A")}
    )

    assert reader.get_recipe("thread-1")["recipe"]["title"] == "A"


# --- Registro de decisões ------------------------------------------------------


def test_decision_store_round_trips_results_with_project_models(backend):
    store = backend.decisions()
    recipe = Recipe(
        dough="massa",
        filling="queijo",
        ingredients=["queijo"],
        preparation="frite",
        utensils=[],
        preparation_methods=["fritar"],
    )
    store.claim("t1", "k1", 0, "fp")
    store.complete("t1", "k1", 0, "fp", {"status": "completed", "recipe": recipe})

    stored = backend.decisions().get("t1", "k1")

    assert stored.completed
    assert stored.result["recipe"] == recipe


def test_decision_store_allows_one_decision_per_version(backend):
    store = backend.decisions()
    store.claim("t1", "k1", 0, "fp")
    store.claim("t1", "k1", 0, "fp")  # mesma chave: sem efeito

    with pytest.raises(VersionAlreadyClaimed):
        store.claim("t1", "k2", 0, "other")

    store.release("t1", "k1")
    store.claim("t1", "k2", 0, "other")
    assert store.get("t1", "k1") is None


# --- Workflow durável ----------------------------------------------------------


def decision(action, version, key, **extra):
    return ImpasseDecision(
        action=action, expected_state_version=version, idempotency_key=key, **extra
    )


def test_impasse_survives_a_restart_and_completes_with_accept(backend, monkeypatch):
    calls = install_fake_agents(monkeypatch)
    paused = backend.session().start(create_initial_state("coxinha", "thread-1"))
    assert paused["status"] == "awaiting_user"

    restarted = backend.session()
    state = restarted.get_state("thread-1")
    assert state["status"] == "awaiting_user"
    assert state["state_version"] == 0

    result = restarted.submit_impasse_decision("thread-1", decision("accept", 0, "accept-1"))

    assert result["status"] == "completed"
    assert backend.session().history.get_recipe("thread-1") is not None
    assert calls == {"chef": 2, "subchef": 2}


def test_repeated_decision_after_restart_returns_the_original_result(backend, monkeypatch):
    calls = install_fake_agents(monkeypatch)
    backend.session().start(create_initial_state("coxinha", "thread-1"))
    first = backend.session().submit_impasse_decision(
        "thread-1", decision("resume", 0, "resume-1", ingredient_additions=["queijo"])
    )
    calls_after_first = dict(calls)

    again = backend.session().submit_impasse_decision(
        "thread-1", decision("resume", 0, "resume-1", ingredient_additions=["queijo"])
    )

    assert first["status"] == again["status"] == "completed"
    assert again["final_response"] == first["final_response"]
    assert calls == calls_after_first


def test_save_then_resume_across_restarts(backend, monkeypatch):
    install_fake_agents(monkeypatch)
    backend.session().start(create_initial_state("coxinha", "thread-1"))

    saved = backend.session().submit_impasse_decision(
        "thread-1", decision("save", 0, "save-1", ingredient_additions=["queijo"])
    )
    assert saved["status"] == "awaiting_user"
    assert saved["state_version"] == 1

    resumed = backend.session().submit_impasse_decision(
        "thread-1", decision("resume", 1, "resume-1")
    )
    assert resumed["status"] == "completed"


def test_stale_pending_claim_from_a_crash_does_not_block_new_decisions(backend, monkeypatch):
    install_fake_agents(monkeypatch)
    backend.session().start(create_initial_state("coxinha", "thread-1"))
    # Simula uma queda entre reservar a versão 0 e aplicar a decisão.
    backend.decisions().claim(
        "thread-1", "lost-key", 0, "fp"
    )

    result = backend.session().submit_impasse_decision(
        "thread-1", decision("cancel", 0, "cancel-1")
    )

    assert result["status"] == "cancelled"


def test_concurrent_decisions_on_the_same_version_allow_only_one(backend, monkeypatch):
    install_fake_agents(monkeypatch)
    session = backend.session()
    session.start(create_initial_state("coxinha", "thread-1"))

    def submit(key):
        try:
            return session.submit_impasse_decision(
                "thread-1", decision("save", 0, key, user_guidance="mais queijo")
            )["status"]
        except StateVersionConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(submit, ["save-a", "save-b"]))

    assert outcomes == ["awaiting_user", "conflict"]


def test_build_session_respects_the_persistence_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("PERSISTENCE", "memory")
    assert build_session().history._store is None

    monkeypatch.setenv("PERSISTENCE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("CHECKPOINT_DATABASE_PATH", str(tmp_path / "checkpoints.db"))
    assert build_session().history._store is not None
    assert (tmp_path / "checkpoints.db").exists()

    monkeypatch.setenv("PERSISTENCE", "postgres")
    with pytest.raises(ValueError, match="DATABASE_URL"):
        build_session()

    monkeypatch.setenv("PERSISTENCE", "mysql")
    with pytest.raises(ValueError, match="PERSISTENCE"):
        build_session()


@pytest.mark.parametrize(
    ("mode", "url", "expected"),
    [
        ("", "", "sqlite"),
        ("", "postgresql://db", "postgres"),
        ("sqlite", "postgresql://db", "sqlite"),
        ("memory", "postgresql://db", "memory"),
    ],
)
def test_persistence_mode(mode, url, expected, monkeypatch):
    monkeypatch.setenv("PERSISTENCE", mode)
    monkeypatch.setenv("DATABASE_URL", url)
    assert persistence_mode() == expected


def test_saved_payload_is_plain_json(backend):
    backend.recipes().save("thread-1", response("Simples"))
    assert json.loads(backend.raw_payload("thread-1"))["recipe"]["title"] == "Simples"
