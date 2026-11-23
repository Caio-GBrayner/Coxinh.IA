import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app, public_image_url
from src.graph import builder as graph_module
from src.recipe_session import RecipeSession
from tests.fakes import install_fake_agents


pytestmark = pytest.mark.usefixtures("stub_cook_llm")


class InlineExecutor:
    """Roda a tarefa na hora: o teste não depende de tempo nem de threads."""

    def submit(self, job):
        job()

    def shutdown(self, wait=True, cancel_futures=False):
        pass


class HeldExecutor(InlineExecutor):
    """Guarda as tarefas sem executar, para observar o estado `running`."""

    def __init__(self):
        self.jobs = []

    def submit(self, job):
        self.jobs.append(job)


@pytest.fixture
def calls(monkeypatch):
    return install_fake_agents(monkeypatch)


@pytest.fixture
def client(calls, tmp_path):
    app = create_app(
        RecipeSession(),
        image_dir=tmp_path,
        cors_origins=["http://localhost:5173"],
        executor=InlineExecutor(),
    )
    with TestClient(app) as test_client:
        yield test_client


def start_paused(client) -> str:
    created = client.post("/recipes", json={"raw_input": "coxinha de batata"})
    assert created.status_code == 202
    thread_id = created.json()["thread_id"]
    state = client.get(f"/recipes/{thread_id}").json()
    assert state["status"] == "awaiting_user"
    return thread_id


def decide(client, thread_id, action, version, key, **extra):
    body = {"action": action, "expected_state_version": version, "idempotency_key": key}
    body.update(extra)
    return client.post(f"/recipes/{thread_id}/impasse", json=body)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_reaches_impasse_with_critique_and_version(client):
    thread_id = start_paused(client)

    state = client.get(f"/recipes/{thread_id}").json()

    assert state["state_version"] == 0
    assert state["critique"] == "Falta um item calórico no recheio."
    assert state["recipe"]["ingredients"] == ["batata"]
    assert state["final_response"] is None


def test_create_rejects_empty_input(client):
    assert client.post("/recipes", json={"raw_input": "   "}).status_code == 422


def test_save_then_resume_completes(client):
    thread_id = start_paused(client)

    saved = decide(client, thread_id, "save", 0, "save-1", ingredient_additions=["queijo"])
    assert saved.status_code == 200
    assert saved.json()["status"] == "awaiting_user"
    assert saved.json()["state_version"] == 1

    resumed = decide(client, thread_id, "resume", 1, "resume-1")
    assert resumed.status_code == 202

    final = client.get(f"/recipes/{thread_id}").json()
    assert final["status"] == "completed"
    assert final["final_response"]["recipe"]["title"]


def test_accept_completes_and_appears_in_history_newest_first(client):
    first = start_paused(client)
    decide(client, first, "accept", 0, "accept-1")
    second = start_paused(client)
    decide(client, second, "accept", 0, "accept-2")

    items = client.get("/recipes").json()["items"]

    assert [item["id"] for item in items] == [second, first]
    assert items[0]["title"]


def test_cancel_is_synchronous(client):
    thread_id = start_paused(client)

    cancelled = decide(client, thread_id, "cancel", 0, "cancel-1")

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_unknown_recipe_returns_404(client):
    assert client.get("/recipes/nope").status_code == 404
    response = decide(client, "nope", "cancel", 0, "k")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "workflow_not_found"


def test_stale_version_returns_409(client):
    thread_id = start_paused(client)

    response = decide(client, thread_id, "cancel", 5, "cancel-1")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "state_version_conflict"


def test_reused_key_with_other_payload_returns_409(client):
    thread_id = start_paused(client)
    decide(client, thread_id, "save", 0, "same-key", user_guidance="mais sal")

    response = decide(client, thread_id, "save", 1, "same-key", user_guidance="outra")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "idempotency_key_reuse"


def test_repeating_an_applied_decision_returns_current_state(client, calls):
    thread_id = start_paused(client)
    decide(client, thread_id, "accept", 0, "accept-1")
    calls_after = dict(calls)

    again = decide(client, thread_id, "accept", 0, "accept-1")

    assert again.status_code == 200
    assert again.json()["status"] == "completed"
    assert calls == calls_after


def test_new_decision_after_completion_returns_409(client):
    thread_id = start_paused(client)
    decide(client, thread_id, "accept", 0, "accept-1")

    response = decide(client, thread_id, "cancel", 0, "cancel-1")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "workflow_not_paused"


def test_invalid_decision_body_returns_422(client):
    thread_id = start_paused(client)
    assert decide(client, thread_id, "save", 0, "save-1").status_code == 422
    assert decide(client, thread_id, "accept", 0, "a", user_guidance="x").status_code == 422
    assert decide(client, thread_id, "explode", 0, "x").status_code == 422


def test_running_recipe_reports_running_and_blocks_decisions(calls, tmp_path):
    held = HeldExecutor()
    app = create_app(RecipeSession(), image_dir=tmp_path, cors_origins=[], executor=held)
    with TestClient(app) as client:
        thread_id = client.post("/recipes", json={"raw_input": "coxinha"}).json()["thread_id"]

        assert client.get(f"/recipes/{thread_id}").json()["status"] == "running"
        blocked = decide(client, thread_id, "cancel", 0, "c")
        assert blocked.status_code == 409
        assert blocked.json()["detail"]["code"] == "workflow_running"

        held.jobs.pop()()
        assert client.get(f"/recipes/{thread_id}").json()["status"] == "awaiting_user"


def test_background_failure_becomes_error_status(monkeypatch, tmp_path):
    def broken_chef(state):
        raise RuntimeError("LLM fora do ar")

    monkeypatch.setattr(graph_module, "chef_node", broken_chef)
    app = create_app(RecipeSession(), image_dir=tmp_path, cors_origins=[], executor=InlineExecutor())
    with TestClient(app) as client:
        thread_id = client.post("/recipes", json={"raw_input": "coxinha"}).json()["thread_id"]
        state = client.get(f"/recipes/{thread_id}").json()

    assert state["status"] == "error"
    assert "LLM fora do ar" in state["error"]


def test_real_image_reference_becomes_public_url(calls, monkeypatch, tmp_path):
    # O grafo é montado ao criar a sessão: o nó precisa ser trocado antes.
    monkeypatch.setattr(
        graph_module,
        "image_node",
        lambda state: {"image_url": "images/abc.png", "image_status": "generated"},
    )
    app = create_app(RecipeSession(), image_dir=tmp_path, cors_origins=[], executor=InlineExecutor())
    with TestClient(app) as client:
        thread_id = start_paused(client)
        decide(client, thread_id, "accept", 0, "accept-1")
        final = client.get(f"/recipes/{thread_id}").json()
        item = client.get("/recipes").json()["items"][0]

    assert final["final_response"]["image"]["url"] == "/images/abc.png"
    assert item["image_url"] == "/images/abc.png"


def test_simulated_reference_is_not_a_url():
    assert public_image_url("simulated://coxinha/abc") is None
    assert public_image_url(None) is None
    assert public_image_url("images/k.png") == "/images/k.png"


def test_serves_stored_images_with_safe_headers(client, tmp_path):
    (tmp_path / "abc123.png").write_bytes(b"\x89PNG fake")

    response = client.get("/images/abc123.png")

    assert response.status_code == 200
    assert response.content == b"\x89PNG fake"
    assert "sandbox" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize(
    "path",
    [
        "/images/missing.png",
        "/images/notes.txt",
        "/images/..%2Fsecret.png",
        "/images/%2e%2e%2fsecret.png",
        "/images/.hidden.png",
    ],
)
def test_image_route_rejects_unknown_and_unsafe_names(client, tmp_path, path):
    (tmp_path.parent / "secret.png").write_bytes(b"secret")
    assert client.get(path).status_code == 404


def test_cors_allows_the_configured_front_origin(client):
    response = client.options(
        "/recipes",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_browsers_share_global_history(client):
    """A cobertura de dois navegadores agora verifica o carrossel global aprovado."""
    thread_id = start_paused(client)
    assert client.get('/recipes').json() == {'items': []}
    decide(client, thread_id, 'accept', 0, 'global-accept')
    with TestClient(client.app) as second:
        assert second.get('/recipes').json()['items'][0]['id'] == thread_id
        assert second.get(f'/recipes/{thread_id}').json()['status'] == 'completed'


def test_save_does_not_run_agents_and_stale_resume_preserves_state(client, calls):
    thread_id = start_paused(client)
    before = dict(calls)
    saved = decide(client, thread_id, 'save', 0, 'save-check', ingredient_additions=['queijo'])
    assert saved.json()['state_version'] == 1
    assert calls == before
    stale = decide(client, thread_id, 'resume', 0, 'stale-resume')
    assert stale.status_code == 409
    assert client.get(f'/recipes/{thread_id}').json() == saved.json()
    assert calls == before


def test_accept_preserves_pipeline_without_rerunning_review(client, calls):
    thread_id = start_paused(client)
    before = dict(calls)
    assert decide(client, thread_id, 'accept', 0, 'accept-pipeline').status_code == 202
    final = client.get(f'/recipes/{thread_id}').json()['final_response']
    assert final['health']
    assert final['image']
    assert calls['chef'] == before['chef']
    assert calls['subchef'] == before['subchef']


def test_local_image_endpoint_rejects_symlink_outside_storage(client, tmp_path):
    outside = tmp_path.parent / 'outside.png'
    outside.write_bytes(b'outside')
    try:
        (tmp_path / 'linked.png').symlink_to(outside)
    except OSError:
        pytest.skip('Symlink creation unavailable on this account.')
    assert client.get('/images/linked.png').status_code == 404
