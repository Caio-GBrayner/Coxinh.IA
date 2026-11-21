from typing import Annotated, Any, Literal, Required, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages

from .schemas import Recipe, SubChefEvaluation


WorkflowStatus = Literal[
    "in_revision",
    "approved",
    "awaiting_user",
    "completed",
    "cancelled",
    "error",
]


class RecipeState(TypedDict, total=False):
    thread_id: Required[str]
    raw_input: Required[str]
    messages: Required[Annotated[list[AnyMessage], add_messages]]
    user_preferences: Required[dict[str, Any]]

    authorized_ingredients: Required[list[str] | None]
    authorized_utensils: Required[list[str] | None]
    authorized_preparation_methods: Required[list[str] | None]

    ingredient_additions: Required[list[str]]
    user_guidance: Required[str | None]
    user_action: Required[Literal["save", "resume", "cancel"] | None]

    recipe: Recipe
    subchef_evaluation: SubChefEvaluation

    recipe_version: Required[int]
    revision_count: Required[int]
    total_attempts: Required[int]
    max_revisions: Required[int]
    status: Required[WorkflowStatus]

    cook_output: dict[str, Any]
    cook_resource_validation: Literal["passed", "incomplete"]
    recipe_steps: str | None
    image_prompt: str | None

    retrieved_health_context: list[dict[str, Any]]
    health_warning: str | None
    health_sources: list[dict[str, Any]]
    health_uncertainty: str | None

    recipe_hash: str | None
    idempotency_key: str | None
    last_impasse_decision_key: str | None
    last_impasse_decision_fingerprint: str | None
    image_url: str | None
    image_status: str | None

    state_version: Required[int]
    state_schema_version: Required[int]
    last_error: str | None
    final_response: dict[str, Any] | None


def create_initial_state(
    raw_input: str,
    thread_id: str,
    *,
    max_revisions: int = 2,
) -> RecipeState:
    if not isinstance(max_revisions, int) or isinstance(max_revisions, bool):
        raise ValueError("max_revisions must be a positive integer.")
    if max_revisions < 1:
        raise ValueError("max_revisions must be a positive integer.")
    if not raw_input.strip():
        raise ValueError("raw_input must not be empty.")
    if not thread_id.strip():
        raise ValueError("thread_id must not be empty.")

    return {
        "thread_id": thread_id,
        "raw_input": raw_input,
        "messages": [HumanMessage(content=raw_input)],
        "user_preferences": {},
        "authorized_ingredients": None,
        "authorized_utensils": None,
        "authorized_preparation_methods": None,
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