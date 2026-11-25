"""API HTTP do Coxinh.IA para o front.

Executar (a partir da raiz do projeto):
    uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8080

A geração de uma receita leva dezenas de segundos, então `POST /recipes` e as
decisões que voltam a rodar os agentes (`resume` e `accept`) respondem 202 e
executam em segundo plano. O front acompanha por `GET /recipes/{thread_id}`.
"""

from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from copy import deepcopy
import logging
import os
from pathlib import Path
import re
from threading import Lock
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

from src.graph.guardrail import GuardResult, InputBlocked
from src.graph.impasse import (
    IdempotencyKeyReuse,
    ImpasseDecision,
    ResumeLimitReached,
    StateVersionConflict,
    WorkflowNotPaused,
)
from src.graph.workflow import RECOVERY_MESSAGE, resume_allowed
from src.persistence.image_store import FileImageStore, ImageStore, build_image_store
from src.recipe_session import RecipeSession
from src.state import create_initial_state
from src.utils.ingredients import split_items


logger = logging.getLogger(__name__)

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"
MAX_WORKERS = 4
IMAGE_NAME = re.compile(r"^[A-Za-z0-9_-]{1,128}\.(png|jpg|jpeg|webp|svg)$")
IMAGE_MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "svg": "image/svg+xml",
}
# Imagens nunca executam nada: SVG servido com sandbox e sem scripts.
IMAGE_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "public, max-age=86400, immutable",
}
FINISHED_STATUSES = {"awaiting_user", "completed", "cancelled", "blocked"}


RawInput = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class CreateRecipeRequest(BaseModel):
    raw_input: RawInput


class RunRegistry:
    """Execuções em segundo plano deste processo: em andamento e falhas."""

    def __init__(self) -> None:
        self._running: set[str] = set()
        self._errors: dict[str, str] = {}
        self._lock = Lock()

    def try_start(self, thread_id: str) -> bool:
        with self._lock:
            if thread_id in self._running:
                return False
            self._running.add(thread_id)
            self._errors.pop(thread_id, None)
            return True

    def finish(self, thread_id: str, error: str | None = None) -> None:
        with self._lock:
            self._running.discard(thread_id)
            if error is not None:
                self._errors[thread_id] = error

    def is_running(self, thread_id: str) -> bool:
        with self._lock:
            return thread_id in self._running

    def error(self, thread_id: str) -> str | None:
        with self._lock:
            return self._errors.get(thread_id)


def public_image_url(reference: object) -> str | None:
    """`images/x.png` vira `/images/x.png`. Referência simulada não é imagem."""
    if isinstance(reference, str) and reference.startswith("images/"):
        return "/" + reference
    return None


def public_response(final_response: dict[str, Any] | None) -> dict[str, Any] | None:
    if final_response is None:
        return None
    response = deepcopy(final_response)
    image = response.get("image")
    if isinstance(image, dict):
        image["url"] = public_image_url(image.get("url"))
    return response


def guardrail_view(state: dict[str, Any]) -> dict[str, Any] | None:
    """Motivo do bloqueio para o front, ou None se o pedido não foi bloqueado."""
    stored = state.get("guardrail")
    if stored is None:
        return None
    result = GuardResult.model_validate(stored)
    if result.allowed:
        return None
    return {"code": result.code, "message": result.message, "reason": result.reason}


def recipe_view(
    thread_id: str,
    state: dict[str, Any],
    api_status: str,
    *,
    notice: str | None = None,
) -> dict[str, Any]:
    """Estado público da receita.

    `notice` explica uma falha técnica recuperada. Ele vai no começo da crítica,
    que é o texto que a tela do Impasse já mostra.
    """
    recipe = state.get("recipe")
    evaluation = state.get("subchef_evaluation")
    rejected = evaluation is not None and getattr(evaluation, "decision", None) == "rejected"
    critique = getattr(evaluation, "critique", None) if rejected else None
    if notice:
        critique = f"{notice} {critique}" if critique else notice
    return {
        "thread_id": thread_id,
        "status": api_status,
        "state_version": state.get("state_version"),
        "recipe": recipe.model_dump(mode="json") if isinstance(recipe, BaseModel) else recipe,
        "critique": critique,
        "evidence": list(getattr(evaluation, "evidence", None) or []) if rejected else [],
        "resume_allowed": resume_allowed(state),
        "ingredient_additions": split_items(state.get("ingredient_additions", [])),
        "user_guidance": state.get("user_guidance"),
        "final_response": public_response(state.get("final_response")),
        "guardrail": guardrail_view(state),
        "error": None,
    }


def problem(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def create_app(
    session: RecipeSession | None = None,
    *,
    image_dir: str | Path | None = None,
    cors_origins: list[str] | None = None,
    executor: ThreadPoolExecutor | None = None,
) -> FastAPI:
    """Fábrica da aplicação. Sem sessão, monta a sessão conforme PERSISTENCE."""
    load_dotenv()
    if session is None:
        from src.persistence.factory import build_session

        session = build_session()

    images: ImageStore = (
        build_image_store() if image_dir is None else FileImageStore(image_dir)
    )
    origins = cors_origins
    if origins is None:
        raw = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
        origins = [origin.strip() for origin in raw.split(",") if origin.strip()]

    pool = executor or ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="recipe")
    registry = RunRegistry()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        pool.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="Coxinh.IA API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def run_in_background(thread_id: str, job: Callable[[], object]) -> None:
        def wrapper() -> None:
            try:
                job()
            except Exception as exc:  # a falha vira estado consultável
                if isinstance(exc, InputBlocked):
                    registry.finish(thread_id, str(exc))
                    return
                logger.exception("Recipe run %s failed", thread_id)
                registry.finish(thread_id, f"{type(exc).__name__}: {exc}")
            else:
                registry.finish(thread_id)

        pool.submit(wrapper)

    def current_view(thread_id: str) -> dict[str, Any]:
        if registry.is_running(thread_id):
            return {"thread_id": thread_id, "status": "running", "error": None}
        error = registry.error(thread_id)
        try:
            state = session.get_state(thread_id)
        except KeyError:
            if error is not None:
                return {"thread_id": thread_id, "status": "error", "error": error}
            raise problem(404, "workflow_not_found", f"No recipe '{thread_id}'.") from None

        state_status = state.get("status")
        notice = state.get("last_error")
        if state_status in FINISHED_STATUSES:
            api_status = state_status
        elif session.is_recoverable(thread_id):
            # Uma decisão do Impasse falhou no meio: a próxima decisão devolve a
            # conversa ao Impasse. Para o front, ela já está aguardando o usuário.
            api_status = "awaiting_user"
            notice = RECOVERY_MESSAGE
        elif error is not None:
            api_status = "error"
        else:
            # Execução parada no meio antes de qualquer Impasse (por exemplo, queda).
            api_status = "interrupted"
        view = recipe_view(thread_id, state, api_status, notice=notice)
        view["error"] = error if api_status in ("error", "awaiting_user") else None
        return view

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/recipes", status_code=status.HTTP_202_ACCEPTED)
    def create_recipe(body: CreateRecipeRequest) -> dict[str, Any]:
        thread_id = f"rcp-{uuid4().hex}"
        initial_state = create_initial_state(body.raw_input, thread_id)
        registry.try_start(thread_id)
        run_in_background(thread_id, lambda: session.start(initial_state))
        return {"thread_id": thread_id, "status": "running"}

    @app.get("/recipes")
    def list_recipes() -> dict[str, Any]:
        items = []
        for entry in reversed(session.history.list_recipes()):
            recipe = entry.get("recipe") or {}
            image = entry.get("image") or {}
            items.append(
                {
                    "id": entry["id"],
                    "title": recipe.get("title"),
                    "subtitle": recipe.get("subtitle"),
                    "image_url": public_image_url(image.get("url")),
                    "image_status": image.get("status"),
                }
            )
        return {"items": items}

    @app.get("/recipes/{thread_id}")
    def get_recipe(thread_id: str) -> dict[str, Any]:
        return current_view(thread_id)

    @app.post("/recipes/{thread_id}/impasse")
    def decide_impasse(thread_id: str, decision: ImpasseDecision) -> JSONResponse:
        if registry.is_running(thread_id):
            raise problem(409, "workflow_running", "The recipe is still running.")
        try:
            known = session.decision_status(thread_id, decision)
        except IdempotencyKeyReuse as exc:
            raise problem(409, "idempotency_key_reuse", str(exc)) from exc
        if known == "done":
            return JSONResponse(current_view(thread_id), status_code=200)

        try:
            state = session.get_state(thread_id)
        except KeyError:
            raise problem(404, "workflow_not_found", f"No recipe '{thread_id}'.") from None

        continuing = state.get("last_impasse_decision_key") == decision.idempotency_key
        if not continuing:
            paused = state.get("status") == "awaiting_user" or session.is_recoverable(thread_id)
            if not paused:
                raise problem(409, "workflow_not_paused", "A receita não está aguardando uma decisão.")
            if decision.expected_state_version != state.get("state_version"):
                raise problem(
                    409,
                    "state_version_conflict",
                    "A receita foi atualizada em outro momento. Confira a versão atual "
                    f"(esperada {decision.expected_state_version}, atual {state.get('state_version')}).",
                )
            if decision.action == "resume" and not resume_allowed(state):
                raise problem(
                    409,
                    "resume_limit_reached",
                    "Limite de novas tentativas atingido. Aceite a proposta atual ou encerre a criação.",
                )

        if decision.action in ("save", "cancel"):
            try:
                session.submit_impasse_decision(thread_id, decision)
            except StateVersionConflict as exc:
                raise problem(409, "state_version_conflict", str(exc)) from exc
            except WorkflowNotPaused as exc:
                raise problem(409, "workflow_not_paused", str(exc)) from exc
            except IdempotencyKeyReuse as exc:
                raise problem(409, "idempotency_key_reuse", str(exc)) from exc
            except ResumeLimitReached as exc:
                raise problem(409, "resume_limit_reached", str(exc)) from exc
            except InputBlocked as exc:
                code = exc.result.code
                http_status = 503 if code == "guard_unavailable" else 422
                raise problem(http_status, code, str(exc)) from exc
            return JSONResponse(current_view(thread_id), status_code=200)

        if not registry.try_start(thread_id):
            raise problem(409, "workflow_running", "The recipe is still running.")
        run_in_background(
            thread_id, lambda: session.submit_impasse_decision(thread_id, decision)
        )
        return JSONResponse({"thread_id": thread_id, "status": "running"}, status_code=202)

    @app.get("/images/{filename}")
    def get_image(filename: str) -> Response:
        match = IMAGE_NAME.fullmatch(filename)
        if match is None:
            raise problem(404, "image_not_found", "Image not found.")
        data = images.read(filename)
        if data is None:
            raise problem(404, "image_not_found", "Image not found.")
        return Response(
            data, media_type=IMAGE_MEDIA_TYPES[match.group(1)], headers=IMAGE_HEADERS
        )

    return app
