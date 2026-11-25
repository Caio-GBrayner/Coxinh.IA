"""Receitas concluídas gravadas em banco, para o carrossel sobreviver a reinícios."""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Protocol

from src.persistence.database import open_connection


logger = logging.getLogger(__name__)

# Versão do formato do payload gravado. Mude ao alterar a resposta final de forma
# incompatível e trate as versões antigas na leitura.
SCHEMA_VERSION = 1


class StoredRecipeError(ValueError):
    """Uma receita gravada não pode ser lida."""


class UnsupportedSchemaVersion(StoredRecipeError):
    """A receita foi gravada por uma versão mais nova da aplicação."""


class CorruptedRecipe(StoredRecipeError):
    """O conteúdo gravado não é um JSON de objeto válido."""


class RecipeRepository(Protocol):
    def save(self, recipe_id: str, response: dict[str, Any]) -> None: ...

    def list(self) -> list[tuple[str, dict[str, Any]]]: ...

    def get(self, recipe_id: str) -> dict[str, Any] | None: ...


class RecipeStore:
    """Tabela `recipes`: uma linha por execução concluída (`thread_id`)."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        with open_connection(self._path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS recipes (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def save(self, recipe_id: str, response: dict[str, Any]) -> None:
        """Grava a resposta final. Repetir o mesmo ID atualiza sem duplicar."""
        payload = json.dumps(response, ensure_ascii=False)
        created_at = datetime.now(timezone.utc).isoformat()
        with open_connection(self._path) as connection:
            connection.execute(
                """
                INSERT INTO recipes (id, created_at, schema_version, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    schema_version = excluded.schema_version,
                    payload = excluded.payload
                """,
                (recipe_id, created_at, SCHEMA_VERSION, payload),
            )

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        """Lista em ordem de gravação. Linhas ilegíveis são puladas e registradas."""
        with open_connection(self._path) as connection:
            rows = connection.execute(
                "SELECT id, schema_version, payload FROM recipes "
                "ORDER BY created_at, rowid"
            ).fetchall()

        recipes = []
        for recipe_id, schema_version, payload in rows:
            try:
                recipes.append((recipe_id, decode_recipe(recipe_id, schema_version, payload)))
            except StoredRecipeError as exc:
                logger.warning("Skipping stored recipe %s: %s", recipe_id, exc)
        return recipes

    def get(self, recipe_id: str) -> dict[str, Any] | None:
        """Busca uma receita. Uma linha ilegível gera erro em vez de sumir."""
        with open_connection(self._path) as connection:
            row = connection.execute(
                "SELECT schema_version, payload FROM recipes WHERE id = ?",
                (recipe_id,),
            ).fetchone()
        if row is None:
            return None
        schema_version, payload = row
        return decode_recipe(recipe_id, schema_version, payload)


def decode_recipe(recipe_id: str, schema_version: int, payload: str) -> dict[str, Any]:
    if schema_version > SCHEMA_VERSION:
        raise UnsupportedSchemaVersion(
            f"Recipe '{recipe_id}' uses schema {schema_version}; "
            f"this version reads up to {SCHEMA_VERSION}."
        )
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CorruptedRecipe(f"Recipe '{recipe_id}' is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise CorruptedRecipe(f"Recipe '{recipe_id}' is not a JSON object.")
    return data
