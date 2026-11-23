"""Monta a sessão da aplicação conforme a variável PERSISTENCE.

- `sqlite` (padrão): checkpoints em `CHECKPOINT_DATABASE_PATH`, receitas e
  decisões do Impasse em `DATABASE_PATH`. Sobrevive a reinícios.
- `memory`: tudo em memória, como no MVP.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

from src.graph.workflow import RecipeWorkflow, project_serializer
from src.persistence.database import (
    DEFAULT_CHECKPOINT_PATH,
    DEFAULT_DATABASE_PATH,
    connect,
    resolve_path,
)
from src.persistence.decision_store import SqliteDecisionStore
from src.persistence.recipe_store import RecipeStore
from src.recipe_history import SessionRecipeHistory
from src.recipe_session import RecipeSession


PERSISTENCE_MODES = ("sqlite", "memory")


def persistence_mode() -> str:
    load_dotenv()
    mode = os.getenv("PERSISTENCE", "").strip().lower() or "sqlite"
    if mode not in PERSISTENCE_MODES:
        raise ValueError(
            f"PERSISTENCE must be one of {', '.join(PERSISTENCE_MODES)}; got '{mode}'."
        )
    return mode


def build_sqlite_session(
    *,
    database_path: str | Path | None = None,
    checkpoint_path: str | Path | None = None,
) -> RecipeSession:
    """Sessão durável: checkpoints, decisões e receitas em SQLite."""
    database = Path(database_path or resolve_path("DATABASE_PATH", DEFAULT_DATABASE_PATH))
    checkpoints = Path(
        checkpoint_path
        or resolve_path("CHECKPOINT_DATABASE_PATH", DEFAULT_CHECKPOINT_PATH)
    )

    serializer = project_serializer()
    # O SqliteSaver mantém uma conexão própria e serializa o acesso com trava interna.
    saver = SqliteSaver(connect(checkpoints, check_same_thread=False), serde=serializer)
    saver.setup()

    workflow = RecipeWorkflow(
        checkpointer=saver,
        decision_store=SqliteDecisionStore(database, serializer),
    )
    history = SessionRecipeHistory(store=RecipeStore(database))
    return RecipeSession(workflow=workflow, history=history)


def build_session() -> RecipeSession:
    """Sessão conforme PERSISTENCE (padrão: sqlite)."""
    if persistence_mode() == "memory":
        return RecipeSession()
    return build_sqlite_session()
