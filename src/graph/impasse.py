from typing import Literal, Self

from langgraph.types import interrupt
from pydantic import BaseModel, Field, model_validator

from src.schemas import NonEmptyText
from src.state import RecipeState


ImpasseAction = Literal["save", "resume", "cancel"]
ImpasseDestination = Literal["chef", "impasse", "end"]


class ImpasseDecision(BaseModel):
    action: ImpasseAction
    expected_state_version: int = Field(ge=0, strict=True)
    idempotency_key: NonEmptyText
    ingredient_additions: list[NonEmptyText] = Field(default_factory=list)
    user_guidance: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_action_payload(self) -> Self:
        if self.action == "save" and not (
            self.ingredient_additions or self.user_guidance
        ):
            raise ValueError(
                "A save action must include an ingredient or user guidance."
            )
        if self.action == "cancel" and (
            self.ingredient_additions or self.user_guidance
        ):
            raise ValueError("A cancel action cannot include workflow updates.")

        return self


class StateVersionConflict(ValueError):
    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(
            f"State version conflict: expected {expected}, current version is {actual}."
        )
        self.expected = expected
        self.actual = actual


def record_impasse_decision(
    state: RecipeState,
    decision: ImpasseDecision,
) -> dict[str, object]:
    if state.get("status") != "awaiting_user":
        raise ValueError("An Impasse decision requires a paused workflow.")

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
    if status == "cancelled" and action == "cancel":
        return "end"

    raise ValueError("The Impasse action does not match the workflow status.")
