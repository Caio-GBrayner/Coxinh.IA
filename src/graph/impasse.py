from typing import Literal, Self

from langgraph.types import interrupt
from pydantic import BaseModel, Field, field_validator, model_validator

from src.schemas import NonEmptyText
from src.state import RecipeState
from src.utils.ingredients import split_items


ImpasseAction = Literal["save", "resume", "accept", "cancel"]
ImpasseDestination = Literal["chef", "impasse", "cook", "end"]


class ImpasseDecision(BaseModel):
    action: ImpasseAction
    expected_state_version: int = Field(ge=0, strict=True)
    idempotency_key: NonEmptyText
    ingredient_additions: list[NonEmptyText] = Field(default_factory=list)
    user_guidance: NonEmptyText | None = None

    @field_validator("ingredient_additions", mode="before")
    @classmethod
    def split_free_text(cls, value: object) -> object:
        """Aceita texto corrido: 'queijo, carne e fogão' vira três itens."""
        if value is None:
            return []
        if isinstance(value, (str, list)):
            return split_items(value)
        return value

    @model_validator(mode="after")
    def validate_action_payload(self) -> Self:
        if self.action == "save" and not (
            self.ingredient_additions or self.user_guidance
        ):
            raise ValueError(
                "A save action must include an ingredient or user guidance."
            )
        if self.action in ("accept", "cancel") and (
            self.ingredient_additions or self.user_guidance
        ):
            raise ValueError(
                f"A {self.action} action cannot include workflow updates."
            )

        return self


class StateVersionConflict(ValueError):
    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(
            f"State version conflict: expected {expected}, current version is {actual}."
        )
        self.expected = expected
        self.actual = actual


class IdempotencyKeyReuse(ValueError):
    """A mesma chave de idempotência foi usada com uma decisão diferente."""


class WorkflowNotPaused(ValueError):
    """A conversa não está aguardando uma decisão do Impasse."""


class ResumeLimitReached(ValueError):
    """A conversa já gastou as novas tentativas; resta aceitar ou encerrar."""


def record_impasse_decision(
    state: RecipeState,
    decision: ImpasseDecision,
) -> dict[str, object]:
    if state.get("status") != "awaiting_user":
        raise WorkflowNotPaused("An Impasse decision requires a paused workflow.")

    current_version = state.get("state_version")
    if (
        not isinstance(current_version, int)
        or isinstance(current_version, bool)
        or current_version < 0
    ):
        raise ValueError("state_version must be a non-negative integer.")
    if decision.expected_state_version != current_version:
        raise StateVersionConflict(decision.expected_state_version, current_version)

    additions = list(state.get("ingredient_additions", []))
    for ingredient in decision.ingredient_additions:
        if ingredient not in additions:
            additions.append(ingredient)

    user_guidance = state.get("user_guidance")
    if decision.user_guidance is not None:
        user_guidance = "\n".join(
            item
            for item in (user_guidance, decision.user_guidance)
            if item is not None
        )

    updates: dict[str, object] = {
        "last_error": None,
        "user_action": decision.action,
        "state_version": current_version + 1,
        "last_impasse_decision_key": decision.idempotency_key,
        "last_impasse_decision_fingerprint": decision.model_dump_json(
            exclude={"idempotency_key"}
        ),
    }
    if decision.ingredient_additions:
        updates["ingredient_additions"] = additions
    if decision.user_guidance is not None:
        updates["user_guidance"] = user_guidance

    if decision.action == "resume":
        updates["revision_count"] = 0
        updates["status"] = "in_revision"
    elif decision.action == "accept":
        updates["status"] = "approved"
    elif decision.action == "cancel":
        updates["status"] = "cancelled"
    else:
        updates["status"] = "awaiting_user"

    return updates


def impasse_node(state: RecipeState) -> dict[str, object]:
    if state.get("status") != "awaiting_user":
        raise ValueError("The Impasse node requires a paused workflow.")

    recipe = state.get("recipe")
    evaluation = state.get("subchef_evaluation")
    decision_payload = interrupt(
        {
            "state_version": state["state_version"],
            "recipe": recipe.model_dump(mode="json") if recipe else None,
            "critique": evaluation.critique if evaluation else None,
            "ingredient_additions": state.get("ingredient_additions", []),
            "user_guidance": state.get("user_guidance"),
        }
    )
    decision = ImpasseDecision.model_validate(decision_payload)
    return record_impasse_decision(state, decision)


def route_after_impasse(state: RecipeState) -> ImpasseDestination:
    status = state.get("status")
    action = state.get("user_action")

    if status == "awaiting_user" and action == "save":
        return "impasse"
    if status == "in_revision" and action == "resume":
        return "chef"
    if status == "approved" and action == "accept":
        return "cook"
    if status == "cancelled" and action == "cancel":
        return "end"

    raise ValueError("The Impasse action does not match the workflow status.")
