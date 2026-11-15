from typing import Annotated, Any, Literal, Required, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages

from .schemas import AvaliacaoSubchef, Receita


StatusFluxo = Literal[
    "in_revision",
    "approved",
    "awaiting_user",
    "completed",
    "cancelled",
    "error",
]


class ReceitaState(TypedDict, total=False):
    # Identificação da conversa e entrada
    thread_id: Required[str]
    raw_input: Required[str]
    messages: Annotated[list[AnyMessage], add_messages]
    user_preferences: dict[str, Any]

    # Recursos autorizados pelo usuário
    ingredientes_autorizados: list[str] | None
    utensilios_autorizados: list[str] | None
    meios_preparo_autorizados: list[str] | None

    # Intervenção humana
    ingredient_additions: list[str]
    user_guidance: str | None
    user_action: Literal["save", "resume", "cancel"] | None

    # Receita e avaliação
    coxinha: Receita
    avaliacao: AvaliacaoSubchef

    # recipe_version starts at 0 and is incremented when the Chef creates a proposal.
    # revision_count counts Chef revisions; total_attempts counts valid SubChef reviews.
    recipe_version: Required[int]
    revision_count: Required[int]
    total_attempts: Required[int]
    max_revisions: Required[int]
    status: Required[StatusFluxo]

    # Cozinheiro
    recipe_steps: str | None
    image_prompt: str | None

    # RAG e aviso de saúde
    retrieved_health_context: list[dict[str, Any]]
    health_warning: str | None
    health_sources: list[dict[str, Any]]
    health_uncertainty: str | None

    # Imagem e idempotência
    recipe_hash: str | None
    idempotency_key: str | None
    image_url: str | None
    image_status: str | None

    # Controle de alterações e formato do estado
    # state_version is incremented atomically by the persistence layer.
    # expected_state_version belongs to an update request, not to this persisted state.
    state_version: Required[int]
    state_schema_version: Required[int]
    last_error: str | None

    # Resultado final
    final_response: dict[str, Any] | None



def criar_estado_inicial(
    raw_input: str,
    thread_id: str,
    *,
    max_revisions: int = 2,
) -> ReceitaState:
    """Create the initial workflow state for a conversation."""
    if not isinstance(max_revisions, int) or isinstance(max_revisions, bool):
        raise ValueError("max_revisions must be a positive integer.")
    if max_revisions < 1:
        raise ValueError("max_revisions must be a positive integer.")

    return {
        "thread_id": thread_id,
        "raw_input": raw_input,
        "messages": [HumanMessage(content=raw_input)],
        "user_preferences": {},
        "ingredientes_autorizados": None,
        "utensilios_autorizados": None,
        "meios_preparo_autorizados": None,
        "ingredient_additions": [],
        "user_guidance": None,
        "user_action": None,
        "recipe_version": 0,
        "revision_count": 0,
        "total_attempts": 0,
        "max_revisions": max_revisions,
        "status": "in_revision",
        "state_version": 0,
        "state_schema_version": 1,
    }