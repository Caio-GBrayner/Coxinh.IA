from unittest.mock import Mock

import pytest

from src.graph import graph as graph_module
from src.schemas import Recipe, SubChefEvaluation
from src.state import RecipeState, create_initial_state


def create_recipe() -> Recipe:
    return Recipe(
        dough="Potato dough",
        filling="Chicken",
        ingredients=["potato", "chicken"],
        preparation="Boil the potatoes and shape the dough.",
        utensils=["pot"],
        preparation_methods=["boiling"],
    )


def build_test_graph(monkeypatch, decisions):
    calls = {"chef": 0, "subchef": 0}

    def fake_chef_node(state: RecipeState) -> dict[str, object]:
        calls["chef"] += 1
        return {
            "recipe": create_recipe(),
            "recipe_version": state["recipe_version"] + 1,
        }

    def fake_subchef_node(state: RecipeState) -> dict[str, object]:
        calls["subchef"] += 1
        decision = decisions[calls["subchef"] - 1]
        return {
            "subchef_evaluation": SubChefEvaluation(
                decision=decision,
                critique="Revise the proposal." if decision == "rejected" else "",
            )
        }

    monkeypatch.setattr(graph_module, "chef_node", fake_chef_node)
    monkeypatch.setattr(graph_module, "subchef_node", fake_subchef_node)

    return graph_module.build_graph(), calls


def test_approval_on_first_attempt_ends_as_approved(monkeypatch):
    workflow, calls = build_test_graph(monkeypatch, ["approved"])
    initial_state = create_initial_state("Make a coxinha.", "thread-1")

    result = workflow.invoke(initial_state)

    assert result["status"] == "approved"
    assert result["revision_count"] == 1
    assert result["total_attempts"] == 1
    assert result["recipe_version"] == 1
    assert calls == {"chef": 1, "subchef": 1}


def test_rejection_then_approval_revises_and_finishes(monkeypatch):
    workflow, calls = build_test_graph(monkeypatch, ["rejected", "approved"])
    initial_state = create_initial_state(
        "Make a coxinha.",
        "thread-1",
        max_revisions=2,
    )

    result = workflow.invoke(initial_state)

    assert result["status"] == "approved"
    assert result["revision_count"] == 2
    assert result["total_attempts"] == 2
    assert result["recipe_version"] == 2
    assert calls == {"chef": 2, "subchef": 2}


def test_rejection_on_last_attempt_ends_at_impasse(monkeypatch):
    workflow, calls = build_test_graph(monkeypatch, ["rejected", "rejected"])
    initial_state = create_initial_state(
        "Make a coxinha.",
        "thread-1",
        max_revisions=2,
    )

    result = workflow.invoke(initial_state)

    assert result["status"] == "awaiting_user"
    assert result["revision_count"] == 2
    assert result["total_attempts"] == 2
    assert result["recipe_version"] == 2
    assert calls == {"chef": 2, "subchef": 2}


def test_approval_on_last_attempt_is_not_blocked_by_limit(monkeypatch):
    workflow, calls = build_test_graph(monkeypatch, ["approved"])
    initial_state = create_initial_state(
        "Make a coxinha.",
        "thread-1",
        max_revisions=1,
    )

    result = workflow.invoke(initial_state)

    assert result["status"] == "approved"
    assert result["revision_count"] == 1
    assert result["total_attempts"] == 1
    assert calls == {"chef": 1, "subchef": 1}


def test_technical_subchef_failure_does_not_record_attempt(monkeypatch):
    def fake_chef_node(state: RecipeState) -> dict[str, object]:
        return {
            "recipe": create_recipe(),
            "recipe_version": state["recipe_version"] + 1,
        }

    monkeypatch.setattr(graph_module, "chef_node", fake_chef_node)
    monkeypatch.setattr(
        graph_module,
        "subchef_node",
        Mock(side_effect=RuntimeError("LLM request failed.")),
    )
    record_evaluation = Mock(
        wraps=graph_module._record_subchef_evaluation_node
    )
    monkeypatch.setattr(
        graph_module,
        "_record_subchef_evaluation_node",
        record_evaluation,
    )
    workflow = graph_module.build_graph()
    initial_state = create_initial_state("Make a coxinha.", "thread-1")

    with pytest.raises(RuntimeError, match="LLM request failed"):
        workflow.invoke(initial_state)

    record_evaluation.assert_not_called()
    assert initial_state["revision_count"] == 0
    assert initial_state["total_attempts"] == 0
