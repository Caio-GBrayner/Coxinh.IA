"""Expõe o fluxo de receitas à interface web durante a execução local."""

from secrets import token_urlsafe
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

from src.graph.impasse import (
    IdempotencyKeyReuse,
    ImpasseDecision,
    StateVersionConflict,
    WorkflowNotPaused,
)
from src.recipe_session import RecipeSession
from src.schemas import NonEmptyText
from src.state import RecipeState, create_initial_state


SESSION_COOKIE = "coxinh_session"


class NewRecipe(BaseModel):
    """Recebe a ideia escrita pela pessoa no formulário."""

    raw_input: NonEmptyText


class SessionStore:
    """Separa os históricos dos navegadores enquanto o processo estiver ativo."""

    def __init__(self) -> None:
        """Cria o índice de sessões protegido para acessos simultâneos."""
        self._sessions: dict[str, RecipeSession] = {}
        self._lock = Lock()

    def get(self, request: Request, response: Response) -> RecipeSession:
        """Recupera a sessão do cookie ou cria uma nova sessão em memória."""
        cookie = request.cookies.get(SESSION_COOKIE)
        with self._lock:
            if cookie is not None and cookie in self._sessions:
                return self._sessions[cookie]

            token = token_urlsafe(32)
            session = RecipeSession()
            self._sessions[token] = session

        response.set_cookie(
            key=SESSION_COOKIE,
            value=token,
            httponly=True,
            samesite="lax",
            path="/api",
        )
        return session


def _present(state: RecipeState) -> dict[str, object]:
    """Devolve somente os campos necessários às telas da execução."""
    recipe = state.get("recipe")
    evaluation = state.get("subchef_evaluation")
    return {
        "thread_id": state["thread_id"],
        "status": state["status"],
        "state_version": state["state_version"],
        "revision_count": state["revision_count"],
        "max_revisions": state["max_revisions"],
        "critique": evaluation.critique if evaluation is not None else None,
        "recipe": recipe.model_dump(mode="json") if recipe is not None else None,
        "ingredient_additions": state.get("ingredient_additions", []),
        "user_guidance": state.get("user_guidance"),
        "final_response": state.get("final_response"),
    }


def create_app(store: SessionStore | None = None) -> FastAPI:
    """Cria a API e permite injetar um índice isolado nos testes."""
    app = FastAPI(title="Coxinh.IA API")
    sessions = store if store is not None else SessionStore()

    @app.post("/api/recipes", status_code=201)
    def create_recipe(payload: NewRecipe, request: Request, response: Response):
        """Inicia uma execução nova com identificador gerado no servidor."""
        session = sessions.get(request, response)
        state = create_initial_state(payload.raw_input, str(uuid4()))
        return _present(session.start(state))

    @app.get("/api/recipes")
    def list_recipes(request: Request, response: Response):
        """Lista apenas as receitas concluídas da sessão do navegador."""
        return sessions.get(request, response).history.list_recipes()

    @app.get("/api/recipes/{thread_id}")
    def get_recipe(thread_id: str, request: Request, response: Response):
        """Consulta a execução associada a esta sessão, inclusive no Impasse."""
        session = sessions.get(request, response)
        try:
            return _present(session.get_state(thread_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Receita não encontrada.") from exc

    @app.post("/api/recipes/{thread_id}/decisions")
    def decide_impasse(
        thread_id: str,
        decision: ImpasseDecision,
        request: Request,
        response: Response,
    ):
        """Salva, retoma ou encerra um Impasse na execução existente."""
        session = sessions.get(request, response)
        try:
            result = session.submit_impasse_decision(thread_id, decision)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Receita não encontrada.") from exc
        except (StateVersionConflict, WorkflowNotPaused, IdempotencyKeyReuse) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _present(result)

    return app


app = create_app()
