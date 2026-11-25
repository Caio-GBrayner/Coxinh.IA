"""Monta a sessão da aplicação conforme a variável PERSISTENCE.

- `sqlite` (padrão sem DATABASE_URL): checkpoints em `CHECKPOINT_DATABASE_PATH`, receitas e
  decisões do Impasse em `DATABASE_PATH`. Sobrevive a reinícios.
- `postgres`: checkpoints, receitas, decisões e imagens no banco de `DATABASE_URL`.
- `memory`: tudo em memória, como no MVP.
"""

from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from src.graph.workflow import RecipeWorkflow, project_serializer
from src.persistence.database import (
    DEFAULT_CHECKPOINT_PATH,
    DEFAULT_DATABASE_PATH,
    connect,
    database_url,
    persistence_mode,
    resolve_path,
)
from src.persistence.decision_store import SqliteDecisionStore
from src.persistence.recipe_store import RecipeStore
from src.recipe_history import SessionRecipeHistory
from src.recipe_session import RecipeSession


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


def build_postgres_session(url: str) -> RecipeSession:
    """Sessão durável: checkpoints, decisões e receitas no mesmo Postgres."""
    from src.persistence.postgres import (
        PostgresCheckpointer,
        PostgresDecisionStore,
        PostgresRecipeStore,
        get_pool,
    )

    pool = get_pool(url)
    serializer = project_serializer()
    saver = PostgresCheckpointer(pool, serde=serializer)
    saver.setup()

    workflow = RecipeWorkflow(
        checkpointer=saver,
        decision_store=PostgresDecisionStore(pool, serializer),
    )
    history = SessionRecipeHistory(store=PostgresRecipeStore(pool))
    return RecipeSession(workflow=workflow, history=history)


def build_session() -> RecipeSession:
    """Sessão conforme PERSISTENCE."""
    mode = persistence_mode()
    if mode == "memory":
        return RecipeSession()
    if mode == "postgres":
        return build_postgres_session(database_url())
    return build_sqlite_session()
