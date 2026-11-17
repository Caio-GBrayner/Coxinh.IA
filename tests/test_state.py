import pytest

from src.state import create_initial_state


def test_initial_state_preserves_request_and_workflow_controls():
    request = "Quero uma coxinha de batata com frango."
    state = create_initial_state(request, "conversation-1")

    assert state["raw_input"] == request
    assert state["thread_id"] == "conversation-1"
    assert len(state["messages"]) == 1
    assert state["messages"][0].content == request
    assert state["messages"][0].type == "human"

    assert state["recipe_version"] == 0
    assert state["revision_count"] == 0
    assert state["total_attempts"] == 0
    assert state["max_revisions"] == 2
    assert state["status"] == "in_revision"
    assert state["state_version"] == 0
    assert state["state_schema_version"] == 1

    assert state["authorized_ingredients"] is None
    assert state["authorized_utensils"] is None
    assert state["authorized_preparation_methods"] is None


def test_revision_limit_can_be_configured():
    state = create_initial_state(
        "Request",
        "conversation-1",
        max_revisions=3,
    )

    assert state["max_revisions"] == 3


@pytest.mark.parametrize("max_revisions", [0, -1, True])
def test_invalid_revision_limit_is_rejected(max_revisions):
    with pytest.raises(ValueError, match="positive integer"):
        create_initial_state(
            "Request",
            "conversation-1",
            max_revisions=max_revisions,
        )


def test_conversations_do_not_share_mutable_collections():
    first = create_initial_state("Request A", "conversation-1")
    second = create_initial_state("Request B", "conversation-2")

    first["ingredient_additions"].append("cheese")
    first["user_preferences"]["tone"] = "playful"
    first["messages"].clear()

    assert second["ingredient_additions"] == []
    assert second["user_preferences"] == {}
    assert len(second["messages"]) == 1
    assert second["messages"][0].content == "Request B"
