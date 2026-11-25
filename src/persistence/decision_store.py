"""Registro das decisões do Impasse: idempotência e uma decisão por versão.

Cada decisão é reservada (`claim`) antes de ser aplicada e concluída
(`complete`) com o resultado. A chave primária `(thread_id, idempotency_key)`
garante que repetir a mesma decisão devolve o resultado original, também depois
de um reinício. A restrição única `(thread_id, state_version)` garante, em uma
única instrução atômica, que só uma decisão é aceita para cada versão do estado.

Uma reserva `pending` que sobrou de uma queda é tratada pelo workflow: a
aplicação roda em um único processo (decisão D4), então uma reserva pendente
encontrada fora da execução atual é necessariamente antiga.
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from threading import Lock
from typing import Any, Protocol

from src.persistence.database import open_connection


@dataclass(frozen=True)
class StoredDecision:
    idempotency_key: str
    fingerprint: str
    state_version: int
    completed: bool
    result: dict[str, Any] | None = None


class VersionAlreadyClaimed(Exception):
    """Outra decisão já reservou esta versão do estado."""

    def __init__(self, existing: StoredDecision) -> None:
        super().__init__(
            f"State version {existing.state_version} already has a decision "
            f"('{existing.idempotency_key}')."
        )
        self.existing = existing


class DecisionStore(Protocol):
    def get(self, thread_id: str, key: str) -> StoredDecision | None: ...

    def claim(
        self, thread_id: str, key: str, state_version: int, fingerprint: str
    ) -> None: ...

    def complete(
        self,
        thread_id: str,
        key: str,
        state_version: int,
        fingerprint: str,
        result: dict[str, Any],
    ) -> None: ...

    def release(self, thread_id: str, key: str) -> None: ...


class InMemoryDecisionStore:
    """Mesmo contrato dos bancos, para testes e para o modo sem persistência."""

    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], StoredDecision] = {}
        self._lock = Lock()

    def get(self, thread_id: str, key: str) -> StoredDecision | None:
        with self._lock:
            stored = self._by_key.get((thread_id, key))
            return _copy(stored)

    def claim(
        self, thread_id: str, key: str, state_version: int, fingerprint: str
    ) -> None:
        with self._lock:
            if (thread_id, key) in self._by_key:
                return
            for (stored_thread, _), stored in self._by_key.items():
                if stored_thread == thread_id and stored.state_version == state_version:
                    raise VersionAlreadyClaimed(_clone(stored))
            self._by_key[(thread_id, key)] = StoredDecision(
                key, fingerprint, state_version, completed=False
            )

    def complete(
        self,
        thread_id: str,
        key: str,
        state_version: int,
        fingerprint: str,
        result: dict[str, Any],
    ) -> None:
        with self._lock:
            self._by_key[(thread_id, key)] = StoredDecision(
                key, fingerprint, state_version, completed=True, result=deepcopy(result)
            )

    def release(self, thread_id: str, key: str) -> None:
        with self._lock:
            stored = self._by_key.get((thread_id, key))
            if stored is not None and not stored.completed:
                del self._by_key[(thread_id, key)]


class SqliteDecisionStore:
    """Tabela `impasse_decisions`, com o resultado serializado como no checkpoint."""

    def __init__(self, path: str | Path, serializer: Any) -> None:
        self._path = Path(path)
        self._serializer = serializer
        with open_connection(self._path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS impasse_decisions (
                    thread_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    state_version INTEGER NOT NULL,
                    fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'completed')),
                    result_type TEXT,
                    result_blob BLOB,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (thread_id, idempotency_key),
                    UNIQUE (thread_id, state_version)
                )
                """
            )

    def get(self, thread_id: str, key: str) -> StoredDecision | None:
        with open_connection(self._path) as connection:
            row = connection.execute(
                "SELECT idempotency_key, fingerprint, state_version, status, "
                "result_type, result_blob FROM impasse_decisions "
                "WHERE thread_id = ? AND idempotency_key = ?",
                (thread_id, key),
            ).fetchone()
        return self._to_decision(row)

    def claim(
        self, thread_id: str, key: str, state_version: int, fingerprint: str
    ) -> None:
        try:
            with open_connection(self._path) as connection:
                connection.execute(
                    "INSERT INTO impasse_decisions (thread_id, idempotency_key, "
                    "state_version, fingerprint, status, created_at) "
                    "VALUES (?, ?, ?, ?, 'pending', ?)",
                    (thread_id, key, state_version, fingerprint, _now()),
                )
        except sqlite3.IntegrityError:
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
        with open_connection(self._path) as connection:
            connection.execute(
                """
                INSERT INTO impasse_decisions (thread_id, idempotency_key,
                    state_version, fingerprint, status, result_type, result_blob,
                    created_at)
                VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
                ON CONFLICT(thread_id, idempotency_key) DO UPDATE SET
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
        with open_connection(self._path) as connection:
            connection.execute(
                "DELETE FROM impasse_decisions WHERE thread_id = ? "
                "AND idempotency_key = ? AND status = 'pending'",
                (thread_id, key),
            )

    def _get_by_version(self, thread_id: str, state_version: int) -> StoredDecision | None:
        with open_connection(self._path) as connection:
            row = connection.execute(
                "SELECT idempotency_key, fingerprint, state_version, status, "
                "result_type, result_blob FROM impasse_decisions "
                "WHERE thread_id = ? AND state_version = ?",
                (thread_id, state_version),
            ).fetchone()
        return self._to_decision(row)

    def _to_decision(self, row: tuple | None) -> StoredDecision | None:
        if row is None:
            return None
        key, fingerprint, state_version, status, result_type, result_blob = row
        result = None
        if status == "completed" and result_type is not None:
            result = self._serializer.loads_typed((result_type, result_blob))
        return StoredDecision(
            key, fingerprint, state_version, completed=status == "completed", result=result
        )


def _copy(stored: StoredDecision | None) -> StoredDecision | None:
    return None if stored is None else _clone(stored)


def _clone(stored: StoredDecision) -> StoredDecision:
    """Cópia independente: quem lê o registro não altera o que está guardado."""
    return StoredDecision(
        stored.idempotency_key,
        stored.fingerprint,
        stored.state_version,
        stored.completed,
        deepcopy(stored.result),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
