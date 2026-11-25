import asyncio
from collections.abc import Callable
import logging
import os
from typing import Any, Literal

from fastmcp import FastMCP
from pydantic import BaseModel, ValidationError

from mcp_server.errors import tool_error
from mcp_server.images import (
    PROMPT_VERSION,
    GeneratedImage,
    ImageProviderError,
    ImageService,
    SimulatedImageProvider,
)
from src.graph.guardrail import InputBlocked
from src.graph.impasse import (
    IdempotencyKeyReuse,
    ImpasseDecision,
    StateVersionConflict,
    WorkflowNotPaused,
)
from src.graph.resource_validation import (
    ResourceValidationResult,
    validate_recipe_resources,
)
from src.recipe_session import RecipeSession
from src.schemas import Recipe


logger = logging.getLogger(__name__)

WebSearch = Callable[[str], list[dict[str, str]]]


class WebResult(BaseModel):
    title: str
    url: str
    content: str


class WebSearchResponse(BaseModel):
    status: Literal["ok", "no_results"]
    results: list[WebResult]


class ImpasseOutcome(BaseModel):
    """Projeção reduzida do estado depois da decisão. Não devolve o estado todo."""

    thread_id: str
    status: str | None
    user_action: str | None
    state_version: int | None
    revision_count: int | None
    total_attempts: int | None
    recipe_version: int | None


def _register_validation(mcp: FastMCP) -> None:
    @mcp.tool(
        name="validate_recipe_resources",
        description=(
            "Compara a receita com os ingredientes, utensílios e métodos "
            "autorizados. Lista nula significa 'não informado' (categoria não "
            "verificada); lista vazia significa 'nenhum autorizado'."
        ),
    )
    def validate(
        recipe: Recipe,
        authorized_ingredients: list[str] | None,
        authorized_utensils: list[str] | None,
        authorized_preparation_methods: list[str] | None,
        ingredient_additions: list[str] | None = None,
    ) -> ResourceValidationResult:
        try:
            return validate_recipe_resources(
                recipe,
                authorized_ingredients=authorized_ingredients,
                authorized_utensils=authorized_utensils,
                authorized_preparation_methods=authorized_preparation_methods,
                ingredient_additions=ingredient_additions or [],
            )
        except ValueError as exc:
            raise tool_error("invalid_input", str(exc)) from exc


def _register_image(mcp: FastMCP, image_service: ImageService) -> None:
    @mcp.tool(
        name="generate_coxinha_image",
        description=(
            "Gera uma imagem ilustrativa fiel à receita final. Repetir a mesma "
            "entrada reutiliza o resultado já gerado. Devolve uma referência, "
            "nunca o binário."
        ),
    )
    async def generate(
        recipe: Recipe,
        image_prompt: str,
        prompt_version: str = PROMPT_VERSION,
    ) -> GeneratedImage:
        if not image_prompt.strip():
            raise tool_error("invalid_input", "image_prompt must not be empty.")
        try:
            return await asyncio.to_thread(
                image_service.generate,
                recipe,
                image_prompt,
                prompt_version=prompt_version,
            )
        except ImageProviderError as exc:
            logger.warning("Image provider unavailable: %s", type(exc).__name__)
            raise tool_error(
                "provider_unavailable", "The image provider is unavailable."
            ) from exc


def _register_search(mcp: FastMCP, web_search: WebSearch) -> None:
    @mcp.tool(
        name="search_web",
        description=(
            "Pesquisa na web e devolve título, URL e trecho. Sem resultado "
            "relevante devolve status 'no_results'; falha do provedor é erro."
        ),
    )
    async def search(query: str) -> WebSearchResponse:
        if not query.strip():
            raise tool_error("invalid_input", "query must not be empty.")
        try:
            raw_results = await asyncio.to_thread(web_search, query)
            results = [WebResult.model_validate(item) for item in raw_results]
        except Exception as exc:
            logger.warning("Web search unavailable: %s", type(exc).__name__)
            raise tool_error(
                "provider_unavailable", "The web search is unavailable."
            ) from exc
        return WebSearchResponse(
            status="ok" if results else "no_results",
            results=results,
        )


def _register_impasse(mcp: FastMCP, session: RecipeSession) -> None:
    @mcp.tool(
        name="record_impasse_decision",
        description=(
            "Registra a ação humana no Impasse. Só a aplicação a chama, depois "
            "de uma ação humana identificada; não deve ser oferecida ao modelo. "
            "Com 'resume', a chamada continua o grafo e pode demorar."
        ),
    )
    async def record(
        thread_id: str,
        action: Literal["save", "resume", "accept", "cancel"],
        expected_state_version: int,
        idempotency_key: str,
        ingredient_additions: list[str] | None = None,
        user_guidance: str | None = None,
    ) -> ImpasseOutcome:
        try:
            decision = ImpasseDecision(
                action=action,
                expected_state_version=expected_state_version,
                idempotency_key=idempotency_key,
                ingredient_additions=ingredient_additions or [],
                user_guidance=user_guidance,
            )
        except ValidationError as exc:
            messages = [error["msg"] for error in exc.errors()]
            raise tool_error(
                "invalid_input", "The decision is invalid.", errors=messages
            ) from exc

        try:
            state = await asyncio.to_thread(
                session.submit_impasse_decision, thread_id, decision
            )
        except KeyError as exc:
            raise tool_error(
                "workflow_not_found",
                f"No workflow exists for thread_id '{thread_id}'.",
            ) from exc
        except StateVersionConflict as exc:
            raise tool_error(
                "state_version_conflict",
                str(exc),
                expected=exc.expected,
                current=exc.actual,
            ) from exc
        except IdempotencyKeyReuse as exc:
            raise tool_error("idempotency_key_reuse", str(exc)) from exc
        except WorkflowNotPaused as exc:
            raise tool_error("workflow_not_paused", str(exc)) from exc
        except InputBlocked as exc:
            raise tool_error(
                "input_blocked", str(exc), guard_code=exc.result.code
            ) from exc
        except ValueError as exc:
            raise tool_error("invalid_input", str(exc)) from exc

        return ImpasseOutcome(
            thread_id=thread_id,
            status=state.get("status"),
            user_action=state.get("user_action"),
            state_version=state.get("state_version"),
            revision_count=state.get("revision_count"),
            total_attempts=state.get("total_attempts"),
            recipe_version=state.get("recipe_version"),
        )


def create_server(
    *,
    image_service: ImageService | None = None,
    web_search: WebSearch | None = None,
    session: RecipeSession | None = None,
    name: str = "coxinh-ia-tools",
) -> FastMCP:
    """Cria o servidor com as ferramentas cujas dependências foram informadas.

    `validate_recipe_resources` sempre existe. As demais só são registradas
    quando a dependência correspondente é passada. `record_impasse_decision`
    exige a sessão da aplicação para registrar as receitas no mesmo histórico.
    """
    # mask_error_details impede que mensagens de exceções inesperadas vazem
    # para o cliente. Apenas os erros do contrato (tool_error) passam intactos.
    mcp = FastMCP(name, mask_error_details=True)
    _register_validation(mcp)
    if image_service is not None:
        _register_image(mcp, image_service)
    if web_search is not None:
        _register_search(mcp, web_search)
    if session is not None:
        _register_impasse(mcp, session)
    return mcp


def build_default_server() -> FastMCP:
    """Servidor do container `mcp`: ferramentas sem estado compartilhado.

    A busca web não é registrada aqui: o nó de saúde chama o Tavily diretamente.
    """
    from mcp_server.openrouter import build_image_provider_from_env

    return create_server(image_service=ImageService(build_image_provider_from_env()))


def main() -> None:
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    build_default_server().run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()
