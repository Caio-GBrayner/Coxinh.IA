"""Modo de persistência e conexões SQLite dos armazenamentos da aplicação.

Cada operação abre e fecha a própria conexão. Isso evita compartilhar um objeto
`sqlite3.Connection` entre threads (a API executa receitas em segundo plano) e
deixa o controle de concorrência para o próprio SQLite: modo WAL para leituras
simultâneas e `busy_timeout` para esperar uma escrita em andamento.
"""

from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3

from dotenv import load_dotenv


DEFAULT_DATABASE_PATH = "data/coxinh.db"
DEFAULT_CHECKPOINT_PATH = "data/checkpoints.db"
BUSY_TIMEOUT_MS = 30_000


PERSISTENCE_MODES = ("sqlite", "postgres", "memory")


def persistence_mode() -> str:
    """Modo pedido em PERSISTENCE; vazio usa Postgres se houver DATABASE_URL."""
    load_dotenv()
    mode = os.getenv("PERSISTENCE", "").strip().lower()
    if not mode:
        return "postgres" if os.getenv("DATABASE_URL", "").strip() else "sqlite"
    if mode not in PERSISTENCE_MODES:
        raise ValueError(
            f"PERSISTENCE must be one of {', '.join(PERSISTENCE_MODES)}; got '{mode}'."
        )
    return mode


def database_url() -> str:
    load_dotenv()
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise ValueError("DATABASE_URL must be set when PERSISTENCE is 'postgres'.")
    return url


def resolve_path(env_name: str, default: str) -> Path:
    """Lê o caminho do banco no ambiente, com um padrão dentro de `data/`."""
    load_dotenv()
    value = os.getenv(env_name, "").strip()
    return Path(value or default)


def connect(path: str | Path, *, check_same_thread: bool = True) -> sqlite3.Connection:
    """Abre uma conexão com WAL e espera por escritas concorrentes."""
    database = Path(path)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        database,
        timeout=BUSY_TIMEOUT_MS / 1000,
        check_same_thread=check_same_thread,
    )
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    return connection


@contextmanager
def open_connection(path: str | Path) -> Iterator[sqlite3.Connection]:
    """Conexão de uma operação: confirma ao sair, desfaz em erro e fecha sempre."""
    connection = connect(path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()
