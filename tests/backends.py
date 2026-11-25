"""Bancos usados pelos testes de persistência.

O SQLite roda sempre. O Postgres roda quando TEST_DATABASE_URL aponta para um
banco descartável; cada teste usa um schema próprio, removido no fim:

    docker run -d --rm --name coxinh-pg-test -e POSTGRES_PASSWORD=test \\
        -p 127.0.0.1:55432:5432 postgres:16-alpine
    TEST_DATABASE_URL=postgresql://postgres:test@127.0.0.1:55432/postgres pytest
"""

from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

import psycopg
import pytest

from src.graph.workflow import project_serializer
from src.persistence import postgres
from src.persistence.decision_store import SqliteDecisionStore
from src.persistence.factory import build_postgres_session, build_sqlite_session
from src.persistence.recipe_store import RecipeStore


class SqliteBackend:
    def __init__(self, directory: Path) -> None:
        self.database = directory / "app.db"
        self.checkpoints = directory / "checkpoints.db"

    def restart(self):
        """Nada a descartar: cada operação abre a própria conexão."""

    def recipes(self):
        return RecipeStore(self.database)

    def decisions(self):
        return SqliteDecisionStore(self.database, project_serializer())

    def session(self):
        return build_sqlite_session(
            database_path=self.database, checkpoint_path=self.checkpoints
        )

    def env(self):
        return {
            "PERSISTENCE": "sqlite",
            "DATABASE_PATH": str(self.database),
            "CHECKPOINT_DATABASE_PATH": str(self.checkpoints),
        }

    def insert_raw_recipe(self, recipe_id, version, payload):
        with sqlite3.connect(self.database) as connection:
            connection.execute(
                "INSERT INTO recipes VALUES (?, '2026-01-01', ?, ?)",
                (recipe_id, version, payload),
            )

    def raw_payload(self, recipe_id):
        with sqlite3.connect(self.database) as connection:
            return connection.execute(
                "SELECT payload FROM recipes WHERE id = ?", (recipe_id,)
            ).fetchone()[0]


class PostgresBackend:
    def __init__(self, url: str) -> None:
        self.url = url

    def restart(self):
        """Descarta o pool, como um processo novo faria."""
        postgres.close_pools()
        return postgres.get_pool(self.url)

    def recipes(self):
        return postgres.PostgresRecipeStore(postgres.get_pool(self.url))

    def decisions(self):
        return postgres.PostgresDecisionStore(
            postgres.get_pool(self.url), project_serializer()
        )

    def session(self):
        self.restart()
        return build_postgres_session(self.url)

    def env(self):
        return {"PERSISTENCE": "postgres", "DATABASE_URL": self.url}

    def insert_raw_recipe(self, recipe_id, version, payload):
        with psycopg.connect(self.url) as connection:
            connection.execute(
                "INSERT INTO recipes (id, created_at, schema_version, payload) "
                "VALUES (%s, now(), %s, %s)",
                (recipe_id, version, payload),
            )

    def raw_payload(self, recipe_id):
        with psycopg.connect(self.url) as connection:
            return connection.execute(
                "SELECT payload FROM recipes WHERE id = %s", (recipe_id,)
            ).fetchone()[0]


@contextmanager
def postgres_backend():
    base_url = os.getenv("TEST_DATABASE_URL", "").strip()
    if not base_url:
        pytest.skip("TEST_DATABASE_URL não definida")
    schema = f"test_{uuid4().hex}"
    with psycopg.connect(base_url, autocommit=True) as connection:
        connection.execute(f"CREATE SCHEMA {schema}")
    separator = "&" if "?" in base_url else "?"
    try:
        yield PostgresBackend(f"{base_url}{separator}options=-csearch_path%3D{schema}")
    finally:
        postgres.close_pools()
        with psycopg.connect(base_url, autocommit=True) as connection:
            connection.execute(f"DROP SCHEMA {schema} CASCADE")
