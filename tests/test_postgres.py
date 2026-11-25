"""O que só vale para o Postgres: conexões perdidas, criação simultânea e imagens."""

from concurrent.futures import ThreadPoolExecutor
import base64

from fastapi.testclient import TestClient
import httpx
import psycopg
from pydantic import SecretStr
import pytest

from mcp_server.images import ImageProviderError
from mcp_server.openrouter import OpenRouterImageProvider
from src.api.app import create_app
from src.graph.impasse import ImpasseDecision
from src.persistence import postgres
from src.persistence.image_store import build_image_store
from src.recipe_session import RecipeSession
from src.state import create_initial_state
from tests.backends import postgres_backend
from tests.fakes import install_fake_agents


pytestmark = pytest.mark.usefixtures("stub_cook_llm")

PNG = b"\x89PNG\r\n\x1a\n\x00\xff"


@pytest.fixture
def database():
    with postgres_backend() as backend:
        yield backend


@pytest.fixture
def store(database, monkeypatch):
    for name, value in database.env().items():
        monkeypatch.setenv(name, value)
    return build_image_store()


def provider(store, calls):
    def respond(_):
        calls.append(1)
        return httpx.Response(
            200, json={"data": [{"b64_json": base64.b64encode(PNG).decode()}]}
        )

    return OpenRouterImageProvider(
        SecretStr("key"), store=store, transport=httpx.MockTransport(respond)
    )


def test_tables_can_be_created_by_several_processes_at_once(database):
    with ThreadPoolExecutor(max_workers=6) as executor:
        pools = list(executor.map(lambda _: postgres._open_pool(database.url), range(6)))
    for pool in pools:
        pool.close()


def test_pool_recovers_after_the_server_drops_connections(database):
    recipes = database.recipes()
    recipes.save("a", {"recipe": {"title": "A"}})
    with psycopg.connect(database.url, autocommit=True) as admin:
        admin.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE pid <> pg_backend_pid() AND datname = current_database()"
        )
    assert recipes.get("a") == {"recipe": {"title": "A"}}


def test_session_pauses_resumes_and_survives_dropped_connections(database, monkeypatch):
    install_fake_agents(monkeypatch)
    session = database.session()
    session.start(create_initial_state("coxinha", "t1"))
    with psycopg.connect(database.url, autocommit=True) as admin:
        admin.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE pid <> pg_backend_pid() AND datname = current_database()"
        )
    assert session.get_state("t1")["status"] == "awaiting_user"


def test_unreachable_database_fails_without_showing_the_password(monkeypatch):
    monkeypatch.setattr(postgres, "STARTUP_TIMEOUT_SECONDS", 1)
    with pytest.raises(Exception) as error:
        postgres.get_pool("postgresql://user:segredo@127.0.0.1:1/db")
    assert "segredo" not in str(error.value)


def test_image_is_generated_once_and_survives_a_restart(database, store):
    calls = []
    first = provider(store, calls).generate("pedido", idempotency_key="abc")
    database.restart()
    again = provider(build_image_store(), calls).generate("pedido", idempotency_key="abc")

    assert first.reference == again.reference == "images/abc.png"
    assert len(calls) == 1


def test_api_serves_the_image_from_the_database(store):
    store.save("abc", ".png", PNG)
    with TestClient(create_app(RecipeSession(), cors_origins=[])) as client:
        response = client.get("/images/abc.png")
        assert response.content == PNG
        assert response.headers["content-type"] == "image/png"
        assert "sandbox" in response.headers["content-security-policy"]
        assert client.get("/images/other.png").status_code == 404


def test_concurrent_saves_keep_the_first_image(store):
    assert store.save("abc", ".png", PNG) == "abc.png"
    assert store.save("abc", ".webp", b"other") == "abc.png"
    assert store.read("abc.png") == PNG


def test_database_failure_becomes_a_provider_error(store):
    store._pool.close()
    with pytest.raises(ImageProviderError):
        provider(store, []).generate("pedido", idempotency_key="abc")


def test_null_character_in_the_request(database, monkeypatch):
    install_fake_agents(monkeypatch)
    session = database.session()
    result = session.start(create_initial_state("coxinha\x00 de queijo", "t1"))
    assert result["status"] == "awaiting_user"

    # O mesmo vale para o texto das decisões, e o fluxo continua.
    saved = session.submit_impasse_decision(
        "t1",
        ImpasseDecision(
            action="save",
            expected_state_version=0,
            idempotency_key="k",
            ingredient_additions=["quei\x00jo"],
            user_guidance="mais\x00 tempo",
        ),
    )
    assert saved["state_version"] == 1
    assert session.get_state("t1")["user_guidance"] == "mais tempo"
