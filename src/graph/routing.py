from typing import Literal

from src.schemas import SubChefEvaluation
from src.state import RecipeState


SubChefDestination = Literal["chef", "cook", "impasse"]


def record_subchef_evaluation(state: RecipeState) -> RecipeState:
    if state.get("status") != "in_revision":
        raise ValueError(
            "A SubChef evaluation can only be recorded while the workflow is in review."
        )

    evaluation = state.get("subchef_evaluation")
    if not isinstance(evaluation, SubChefEvaluation):
        raise TypeError("State must contain a valid SubChef evaluation.")

    revision_count = state.get("revision_count")
    total_attempts = state.get("total_attempts")
    max_revisions = state.get("max_revisions")

    if not isinstance(revision_count, int) or isinstance(revision_count, bool):
        raise ValueError("revision_count must be a non-negative integer.")
    if revision_count < 0:
        raise ValueError("revision_count must be a non-negative integer.")
    if not isinstance(total_attempts, int) or isinstance(total_attempts, bool):
        raise ValueError("total_attempts must be a non-negative integer.")
    if total_attempts < 0:
        raise ValueError("total_attempts must be a non-negative integer.")
    if not isinstance(max_revisions, int) or isinstance(max_revisions, bool):
        raise ValueError("max_revisions must be a positive integer.")
    if max_revisions < 1:
        raise ValueError("max_revisions must be a positive integer.")
    if revision_count >= max_revisions:
        raise ValueError("No review attempts remain in the current cycle.")

    updated_revision_count = revision_count + 1
    updated_state: RecipeState = {
        **state,
        "revision_count": updated_revision_count,
        "total_attempts": total_attempts + 1,
    }

    if evaluation.decision == "approved":
        updated_state["status"] = "approved"
    elif updated_revision_count < max_revisions:
        updated_state["status"] = "in_revision"
    else:
        updated_state["status"] = "awaiting_user"

    return updated_state


def route_after_subchef(state: RecipeState) -> SubChefDestination:
    evaluation = state.get("subchef_evaluation")
    if not isinstance(evaluation, SubChefEvaluation):
        raise TypeError("State must contain a valid SubChef evaluation.")

    status = state.get("status")
    if evaluation.decision == "approved" and status == "approved":
        return "cook"
    if evaluation.decision == "rejected" and status == "in_revision":
        return "chef"
    if evaluation.decision == "rejected" and status == "awaiting_user":
        return "impasse"

    raise ValueError("The SubChef decision does not match the workflow status.")
