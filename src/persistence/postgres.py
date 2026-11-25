"""Armazenamentos em Postgres: receitas, decisões do Impasse e imagens.

Mesmos contratos das versões em SQLite e em disco. As conexões vêm de um pool
por URL e por processo, com autocommit: cada instrução é uma transação.
"""

import atexit
from datetime import datetime, timezone
import json
import logging
from threading import Lock
from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import ChannelVersions, Checkpoint, CheckpointMetadata
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg.errors import UniqueViolation
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool

from src.persistence.decision_store import StoredDecision, VersionAlreadyClaimed
from src.persistence.recipe_store import SCHEMA_VERSION, StoredRecipeError, decode_recipe


logger = logging.getLogger(__name__)

PostgresPool = ConnectionPool[Connection[DictRow]]

POOL_MAX_SIZE = 10
CONNECT_TIMEOUT_SECONDS = 10
POOL_TIMEOUT_SECONDS = 15
STARTUP_TIMEOUT_SECONDS = 60
# Identificador arbitrário da trava que serializa a criação das tabelas.
SCHEMA_LOCK_ID = 726_419_001

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS recipes (
        id TEXT PRIMARY KEY,
        position BIGINT GENERATED ALWAYS AS IDENTITY,
        created_at TIMESTAMPTZ NOT NULL,
        schema_version INTEGER NOT NULL,
        payload TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS impasse_decisions (
        thread_id TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        state_version INTEGER NOT NULL,
        fingerprint TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('pending', 'completed')),
        result_type TEXT,
        result_blob BYTEA,
        created_at TIMESTAMPTZ NOT NULL,
        PRIMARY KEY (thread_id, idempotency_key),
        UNIQUE (thread_id, state_version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS images (
        idempotency_key TEXT PRIMARY KEY,
        filename TEXT NOT NULL UNIQUE,
        data BYTEA NOT NULL,
        created_at TIMESTAMPTZ NOT NULL
    )
    """,
)

_pools: dict[str, PostgresPool] = {}
_pools_lock = Lock()


def get_pool(url: str) -> PostgresPool:
    """Pool compartilhado da URL, com as tabelas da aplicação já criadas."""
    with _pools_lock:
        pool = _pools.get(url)
        if pool is None:
            pool = _open_pool(url)
            _pools[url] = pool
        return pool


def close_pools() -> None:
    """Fecha as conexões deste processo."""
    with _pools_lock:
        for pool in _pools.values():
            pool.close()
        _pools.clear()


# Sem isso, o encerramento do processo espera até 20 s pelas threads do pool.
atexit.register(close_pools)


def _open_pool(url: str) -> PostgresPool:
    pool = ConnectionPool(
        url,
        min_size=1,
        max_size=POOL_MAX_SIZE,
        timeout=POOL_TIMEOUT_SECONDS,
        # Bancos gerenciados suspendem e derrubam conexões ociosas: testa antes de usar.
        check=ConnectionPool.check_connection,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
            "connect_timeout": CONNECT_TIMEOUT_SECONDS,
            # Sem prepared statements, para funcionar atrás do PgBouncer (Neon, Supabase).
            "prepare_threshold": None,
        },
        open=False,
    )
    # O row_factory em kwargs não é visto pelo verificador de tipos.
    pool = cast(PostgresPool, pool)
    try:
        pool.open(wait=True, timeout=STARTUP_TIMEOUT_SECONDS)
        with pool.connection() as connection, connection.transaction():
            # `api` e `mcp` podem subir juntos, e CREATE IF NOT EXISTS não é
            # seguro contra criação simultânea.
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (SCHEMA_LOCK_ID,))
            for statement in SCHEMA:
                connection.execute(statement)
    except BaseException:
        pool.close()
        raise
    return pool


class PostgresCheckpointer(PostgresSaver):
    """Remove o caractere nulo dos textos, que o JSONB do Postgres não aceita."""

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        values = {
            name: value.replace("\x00", "") if isinstance(value, str) else value
            for name, value in checkpoint["channel_values"].items()
        }
        return super().put(
            config, {**checkpoint, "channel_values": values}, metadata, new_versions
        )


class PostgresRecipeStore:
    """Tabela `recipes`: uma linha por execução concluída (`thread_id`)."""

    def __init__(self, pool: PostgresPool) -> None:
        self._pool = pool

    def save(self, recipe_id: str, response: dict[str, Any]) -> None:
        """Grava a resposta final. Repetir o mesmo ID atualiza sem duplicar."""
        payload = json.dumps(response, ensure_ascii=False)
        with self._pool.connection() as connection:
            connection.execute(
                """
                INSERT INTO recipes (id, created_at, schema_version, payload)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    schema_version = excluded.schema_version,
                    payload = excluded.payload
                """,
                (recipe_id, _now(), SCHEMA_VERSION, payload),
            )

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        """Lista em ordem de gravação. Linhas ilegíveis são puladas e registradas."""
        with self._pool.connection() as connection:
            rows = connection.execute(
                "SELECT id, schema_version, payload FROM recipes ORDER BY position"
            ).fetchall()

        recipes = []
        for row in rows:
            try:
                recipe = decode_recipe(row["id"], row["schema_version"], row["payload"])
            except StoredRecipeError as exc:
                logger.warning("Skipping stored recipe %s: %s", row["id"], exc)
            else:
                recipes.append((row["id"], recipe))
        return recipes

    def get(self, recipe_id: str) -> dict[str, Any] | None:
        """Busca uma receita. Uma linha ilegível gera erro em vez de sumir."""
        with self._pool.connection() as connection:
            row = connection.execute(
                "SELECT schema_version, payload FROM recipes WHERE id = %s",
                (recipe_id,),
            ).fetchone()
        if row is None:
            return None
        return decode_recipe(recipe_id, row["schema_version"], row["payload"])


class PostgresDecisionStore:
    """Tabela `impasse_decisions`, com o resultado serializado como no checkpoint."""

    def __init__(self, pool: PostgresPool, serializer: Any) -> None:
        self._pool = pool
        self._serializer = serializer

    def get(self, thread_id: str, key: str) -> StoredDecision | None:
        with self._pool.connection() as connection:
            row = connection.execute(
                "SELECT * FROM impasse_decisions "
                "WHERE thread_id = %s AND idempotency_key = %s",
                (thread_id, key),
            ).fetchone()
        return self._to_decision(row)

    def claim(
        self, thread_id: str, key: str, state_version: int, fingerprint: str
    ) -> None:
        try:
            with self._pool.connection() as connection:
                connection.execute(
                    "INSERT INTO impasse_decisions (thread_id, idempotency_key, "
                    "state_version, fingerprint, status, created_at) "
                    "VALUES (%s, %s, %s, %s, 'pending', %s)",
                    (thread_id, key, state_version, fingerprint, _now()),
                )
        except UniqueViolation:
            if self.get(thread_id, key) is not None:
                return
            existing = self._get_by_version(thread_id, state_version)
            if existing is None:
                raise
            raise VersionAlreadyClaimed(existing) from None

    def complete(
        self,
        thread_id: str,
        key: str,
        state_version: int,
        fingerprint: str,
        result: dict[str, Any],
    ) -> None:
        result_type, result_blob = self._serializer.dumps_typed(result)
        with self._pool.connection() as connection:
            connection.execute(
                """
                INSERT INTO impasse_decisions (thread_id, idempotency_key,
                    state_version, fingerprint, status, result_type, result_blob,
                    created_at)
                VALUES (%s, %s, %s, %s, 'completed', %s, %s, %s)
                ON CONFLICT (thread_id, idempotency_key) DO UPDATE SET
                    status = 'completed',
                    result_type = excluded.result_type,
                    result_blob = excluded.result_blob
                """,
                (
                    thread_id,
                    key,
                    state_version,
                    fingerprint,
                    result_type,
                    result_blob,
                    _now(),
                ),
            )

    def release(self, thread_id: str, key: str) -> None:
        with self._pool.connection() as connection:
            connection.execute(
                "DELETE FROM impasse_decisions WHERE thread_id = %s "
                "AND idempotency_key = %s AND status = 'pending'",
                (thread_id, key),
            )

    def _get_by_version(self, thread_id: str, state_version: int) -> StoredDecision | None:
        with self._pool.connection() as connection:
            row = connection.execute(
                "SELECT * FROM impasse_decisions "
                "WHERE thread_id = %s AND state_version = %s",
                (thread_id, state_version),
            ).fetchone()
        return self._to_decision(row)

    def _to_decision(self, row: DictRow | None) -> StoredDecision | None:
        if row is None:
            return None
        completed = row["status"] == "completed"
        result = None
        if completed and row["result_type"] is not None:
            result = self._serializer.loads_typed((row["result_type"], row["result_blob"]))
        return StoredDecision(
            row["idempotency_key"],
            row["fingerprint"],
            row["state_version"],
            completed=completed,
            result=result,
        )


class PostgresImageStore:
    """Tabela `images`: o binário da imagem, para não depender de disco."""

    def __init__(self, pool: PostgresPool) -> None:
        self._pool = pool

    def find(self, key: str) -> str | None:
        with self._pool.connection() as connection:
            row = connection.execute(
                "SELECT filename FROM images WHERE idempotency_key = %s", (key,)
            ).fetchone()
        return None if row is None else row["filename"]

    def save(self, key: str, extension: str, data: bytes) -> str:
        """Grava uma vez por chave; se outra gravação chegou antes, vale a primeira."""
        with self._pool.connection() as connection:
            connection.execute(
                "INSERT INTO images (idempotency_key, filename, data, created_at) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (idempotency_key) DO NOTHING",
                (key, f"{key}{extension}", data, _now()),
            )
        return self.find(key) or f"{key}{extension}"

    def read(self, filename: str) -> bytes | None:
        with self._pool.connection() as connection:
            row = connection.execute(
                "SELECT data FROM images WHERE filename = %s", (filename,)
            ).fetchone()
        return None if row is None else row["data"]


def _now() -> datetime:
    return datetime.now(timezone.utc)
