from typing import Literal
import pytest

from src.graph.routing import record_subchef_evaluation, route_after_subchef
from src.schemas import SubChefEvaluation
from src.state import RecipeState, create_initial_state


def state_with_evaluation(
    decision: Literal["approved", "rejected"],
    max_revisions: int = 2,
) -> RecipeState:
    state = create_initial_state("I want a creative coxinha.", "thread-1")
    state["max_revisions"] = max_revisions
    state["subchef_evaluation"] = SubChefEvaluation(
        decision=decision,
        critique="Revise the proposal." if decision == "rejected" else "",
    )
    return state


def test_approval_routes_to_cook_and_counts_review():
    state = state_with_evaluation("approved", max_revisions=1)

    updated = record_subchef_evaluation(state)

    assert updated["revision_count"] == 1
    assert updated["total_attempts"] == 1
    assert updated["status"] == "approved"
    assert route_after_subchef(updated) == "cook"


def test_rejection_with_revisions_remaining_routes_to_chef():
    state = state_with_evaluation("rejected", max_revisions=2)

    updated = record_subchef_evaluation(state)

    assert updated["revision_count"] == 1
    assert updated["total_attempts"] == 1
    assert updated["status"] == "in_revision"
    assert route_after_subchef(updated) == "chef"


def test_rejection_on_last_allowed_attempt_routes_to_impasse():
    state = state_with_evaluation("rejected", max_revisions=1)
    updated = record_subchef_evaluation(state)

    assert updated["revision_count"] == 1
    assert updated["total_attempts"] == 1
    assert updated["status"] == "awaiting_user"
    assert route_after_subchef(updated) == "impasse"


def test_two_review_attempts_are_allowed_before_impasse():
    state = state_with_evaluation("rejected", max_revisions=2)
    first_review = record_subchef_evaluation(state)
    second_review: RecipeState = {
        **first_review,
        "subchef_evaluation": SubChefEvaluation(
            decision="rejected",
            critique="The proposal still needs revision.",
        ),
    }
    updated = record_subchef_evaluation(second_review)

    assert first_review["revision_count"] == 1
    assert first_review["total_attempts"] == 1
    assert route_after_subchef(first_review) == "chef"
    assert updated["revision_count"] == 2
    assert updated["total_attempts"] == 2
    assert route_after_subchef(updated) == "impasse"


def test_approval_on_last_allowed_attempt_still_routes_to_cook():
    state = state_with_evaluation("approved", max_revisions=2)
    state["revision_count"] = 1
    state["total_attempts"] = 1

    updated = record_subchef_evaluation(state)

    assert updated["revision_count"] == 2
    assert updated["total_attempts"] == 2
    assert route_after_subchef(updated) == "cook"


def test_missing_evaluation_does_not_consume_attempt():
    state = create_initial_state("Request", "thread-1")

    with pytest.raises(TypeError, match="valid SubChef evaluation"):
        record_subchef_evaluation(state)

    assert state["revision_count"] == 0
    assert state["total_attempts"] == 0


def test_evaluation_cannot_be_recorded_outside_review_status():
    state = state_with_evaluation("rejected")
    state["status"] = "awaiting_user"

    with pytest.raises(ValueError, match="workflow is in review"):
        record_subchef_evaluation(state)

    assert state["revision_count"] == 0
    assert state["total_attempts"] == 0


@pytest.mark.parametrize(
    "field, value",
    [
        ("revision_count", -1),
        ("total_attempts", -1),
        ("max_revisions", 0),
        ("max_revisions", -1),
        ("revision_count", 3),
        ("revision_count", 2),
    ],
)
def test_invalid_counters_are_rejected(field, value):
    state = state_with_evaluation("rejected")
    state[field] = value

    with pytest.raises(ValueError):
        record_subchef_evaluation(state)


def test_recording_evaluation_does_not_mutate_original_state():
    state = state_with_evaluation("rejected")

    record_subchef_evaluation(state)

    assert state["revision_count"] == 0
    assert state["total_attempts"] == 0
