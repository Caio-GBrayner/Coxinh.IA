"""Verifica o contrato HTTP com agentes e fontes simulados."""

from fastapi.testclient import TestClient

from src.api import SessionStore, create_app
from test_checkpoint import create_in_memory_workflow


def test_browser_sessions_keep_their_recipes_separate(monkeypatch, stub_cook_llm):
    """Uma receita criada em um navegador não aparece no histórico do outro."""
    create_in_memory_workflow(monkeypatch, ["approved", "approved"])
    app = create_app(SessionStore())
    first = TestClient(app)
    second = TestClient(app)

    created = first.post("/api/recipes", json={"raw_input": "Frango"})

    assert created.status_code == 201
    assert created.json()["status"] == "completed"
    recipe_id = created.json()["thread_id"]
    assert first.get(f"/api/recipes/{recipe_id}").status_code == 200
    assert [item["id"] for item in first.get("/api/recipes").json()] == [recipe_id]
    assert second.get("/api/recipes").json() == []
    assert second.get(f"/api/recipes/{recipe_id}").status_code == 404


def test_impasse_saves_then_resumes_in_the_same_session(
    monkeypatch, stub_cook_llm
):
    """Salvar mantém a pausa; retomar conclui e um conflito não altera o estado."""
    _, calls = create_in_memory_workflow(
        monkeypatch, ["rejected", "rejected", "approved"]
    )
    client = TestClient(create_app(SessionStore()))
    created = client.post("/api/recipes", json={"raw_input": "Coxinha estranha"})
    assert created.status_code == 201
    assert created.json()["status"] == "awaiting_user"
    recipe_id = created.json()["thread_id"]
    assert client.get("/api/recipes").json() == []

    saved = client.post(
        f"/api/recipes/{recipe_id}/decisions",
        json={
            "action": "save",
            "expected_state_version": 0,
            "idempotency_key": "save-1",
            "ingredient_additions": ["cogumelo"],
        },
    )
    assert saved.status_code == 200
    assert saved.json()["status"] == "awaiting_user"
    assert saved.json()["state_version"] == 1
    assert calls == {"chef": 2, "subchef": 2}

    stale = client.post(
        f"/api/recipes/{recipe_id}/decisions",
        json={
            "action": "resume",
            "expected_state_version": 0,
            "idempotency_key": "resume-old",
        },
    )
    assert stale.status_code == 409
    assert client.get(f"/api/recipes/{recipe_id}").json()["state_version"] == 1

    resumed = client.post(
        f"/api/recipes/{recipe_id}/decisions",
        json={
            "action": "resume",
            "expected_state_version": 1,
            "idempotency_key": "resume-1",
        },
    )
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "completed"
    assert resumed.json()["final_response"]["recipe"]["title"]
    assert len(client.get("/api/recipes").json()) == 1
