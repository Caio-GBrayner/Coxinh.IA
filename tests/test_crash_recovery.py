"""Teste de queda (item 3.5): derrubar a API no meio do Impasse e retomar.

Sobe a API em um processo separado, com agentes falsos e um banco temporário
(SQLite ou Postgres), mata o processo com SIGKILL e sobe outro sobre o mesmo banco.
"""

import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]
STARTUP_TIMEOUT = 30.0
RUN_TIMEOUT = 30.0


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ApiProcess:
    def __init__(self, data_dir: Path, database_env: dict[str, str]) -> None:
        self.database_env = database_env
        self.data_dir = data_dir
        self.port = free_port()
        self.process: subprocess.Popen | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        env = {
            **os.environ,
            "PYTHONPATH": str(ROOT),
            **self.database_env,
            "IMAGE_STORAGE_DIR": str(self.data_dir / "images"),
            # Vazias e não removidas: o load_dotenv() do processo não sobrescreve.
            "LANGFUSE_PUBLIC_KEY": "",
            "LANGFUSE_SECRET_KEY": "",
            "LANGSMITH_TRACING": "false",
            "OPENROUTER_API_KEY": "",
            "MCP_SERVER_URL": "",
        }
        self.process = subprocess.Popen(
            [sys.executable, "-m", "tests.crash_server", "--port", str(self.port)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(self.process.stderr.read().decode(errors="replace"))
            try:
                if httpx.get(f"{self.url}/health", timeout=1).status_code == 200:
                    return
            except httpx.HTTPError:
                time.sleep(0.2)
        raise TimeoutError("API did not start in time.")

    def crash(self) -> None:
        """SIGKILL: sem desligamento limpo, como uma queda de verdade."""
        assert self.process is not None
        self.process.kill()
        self.process.wait(timeout=10)

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)


@pytest.fixture
def api(tmp_path, backend):
    process = ApiProcess(tmp_path, backend.env())
    yield process
    process.stop()


def wait_for(api: ApiProcess, thread_id: str, wanted: str) -> dict:
    deadline = time.monotonic() + RUN_TIMEOUT
    while time.monotonic() < deadline:
        state = httpx.get(f"{api.url}/recipes/{thread_id}", timeout=5).json()
        if state["status"] == wanted:
            return state
        if state["status"] in ("error", "interrupted"):
            raise AssertionError(f"Unexpected status: {state}")
        time.sleep(0.2)
    raise TimeoutError(f"Recipe {thread_id} did not reach '{wanted}'.")


def test_api_resumes_an_impasse_after_being_killed(api):
    api.start()
    thread_id = httpx.post(
        f"{api.url}/recipes", json={"raw_input": "coxinha de batata"}, timeout=5
    ).json()["thread_id"]
    paused = wait_for(api, thread_id, "awaiting_user")
    assert paused["state_version"] == 0

    api.crash()
    api.start()

    after_crash = httpx.get(f"{api.url}/recipes/{thread_id}", timeout=5).json()
    assert after_crash["status"] == "awaiting_user"
    assert after_crash["state_version"] == 0
    assert after_crash["critique"] == paused["critique"]

    decision = {"action": "accept", "expected_state_version": 0, "idempotency_key": "accept-1"}
    accepted = httpx.post(
        f"{api.url}/recipes/{thread_id}/impasse", json=decision, timeout=5
    )
    assert accepted.status_code == 202
    completed = wait_for(api, thread_id, "completed")
    assert completed["final_response"]["recipe"]["title"] == "Coxinha de teste"

    api.crash()
    api.start()

    # A receita continua no carrossel e repetir a decisão não roda nada de novo.
    items = httpx.get(f"{api.url}/recipes", timeout=5).json()["items"]
    assert [item["id"] for item in items] == [thread_id]
    repeated = httpx.post(
        f"{api.url}/recipes/{thread_id}/impasse", json=decision, timeout=5
    )
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "completed"
