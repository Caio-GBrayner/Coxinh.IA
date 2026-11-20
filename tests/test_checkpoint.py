from concurrent.futures import ThreadPoolExecutor

import pytest

from src.graph import graph as graph_module
from src.graph.impasse import ImpasseDecision, StateVersionConflict
from src.graph.workflow import InMemoryWorkflow
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


def create_in_memory_workflow(monkeypatch, decisions):
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
    return InMemoryWorkflow(), calls


def create_decision(
    action: str,
    *,
    expected_state_version: int,
    idempotency_key: str,
    ingredient_additions: list[str] | None = None,
    user_guidance: str | None = None,
) -> ImpasseDecision:
    return ImpasseDecision(
        action=action,
        expected_state_version=expected_state_version,
        idempotency_key=idempotency_key,
        ingredient_additions=ingredient_additions or [],
        user_guidance=user_guidance,
    )


def test_workflow_pauses_at_impasse_and_save_does_not_restart_agents(monkeypatch):
    workflow, calls = create_in_memory_workflow(
        monkeypatch,
        ["rejected", "rejected"],
    )
    initial_state = create_initial_state(
        "Make a coxinha.",
        "thread-1",
        max_revisions=2,
    )

    result = workflow.start(initial_state)

    assert result["status"] == "awaiting_user"
    assert calls == {"chef": 2, "subchef": 2}

    saved = workflow.submit_impasse_decision(
        "thread-1",
        create_decision(
            "save",
            expected_state_version=0,
            idempotency_key="save-1",
            ingredient_additions=["mushroom"],
            user_guidance="Keep the filling savory.",
        ),
    )

    assert saved["status"] == "awaiting_user"
    assert saved["state_version"] == 1
    assert saved["revision_count"] == 2
    assert saved["total_attempts"] == 2
    assert saved["ingredient_additions"] == ["mushroom"]
    assert saved["user_guidance"] == "Keep the filling savory."
    assert calls == {"chef": 2, "subchef": 2}


def test_resume_starts_a_new_cycle_at_chef_and_subchef(monkeypatch):
    workflow, calls = create_in_memory_workflow(
        monkeypatch,
        ["rejected", "rejected", "approved"],
    )
    workflow.start(
        create_initial_state(
            "Make a coxinha.",
            "thread-1",
            max_revisions=2,
        )
    )

    result = workflow.submit_impasse_decision(
        "thread-1",
        create_decision(
            "resume",
            expected_state_version=0,
            idempotency_key="resume-1",
            ingredient_additions=["mushroom"],
        ),
    )

    assert result["status"] == "approved"
    assert result["user_action"] == "resume"
    assert result["state_version"] == 1
    assert result["revision_count"] == 1
    assert result["total_attempts"] == 3
    assert result["recipe_version"] == 3
    assert result["ingredient_additions"] == ["mushroom"]
    assert calls == {"chef": 3, "subchef": 3}


def test_cancel_ends_workflow_without_restarting_agents(monkeypatch):
    workflow, calls = create_in_memory_workflow(
        monkeypatch,
        ["rejected", "rejected"],
    )
    workflow.start(
        create_initial_state(
            "Make a coxinha.",
            "thread-1",
            max_revisions=2,
        )
    )

    result = workflow.submit_impasse_decision(
        "thread-1",
        create_decision(
            "cancel",
            expected_state_version=0,
            idempotency_key="cancel-1",
        ),
    )

    assert result["status"] == "cancelled"
    assert result["state_version"] == 1
    assert calls == {"chef": 2, "subchef": 2}


def test_stale_state_version_is_rejected_without_resuming(monkeypatch):
    workflow, _ = create_in_memory_workflow(
        monkeypatch,
        ["rejected", "rejected"],
    )
    workflow.start(
        create_initial_state(
            "Make a coxinha.",
            "thread-1",
            max_revisions=2,
        )
    )

    with pytest.raises(StateVersionConflict, match="expected 1, current version is 0"):
        workflow.submit_impasse_decision(
            "thread-1",
            create_decision(
                "save",
                expected_state_version=1,
                idempotency_key="stale-save",
                ingredient_additions=["mushroom"],
            ),
        )

    state = workflow.get_state("thread-1")
    assert state["status"] == "awaiting_user"
    assert state["state_version"] == 0
    assert state["ingredient_additions"] == []


def test_duplicate_impasse_decision_is_idempotent(monkeypatch):
    workflow, calls = create_in_memory_workflow(
        monkeypatch,
        ["rejected", "rejected"],
    )
    workflow.start(
        create_initial_state(
            "Make a coxinha.",
            "thread-1",
            max_revisions=2,
        )
    )
    decision = create_decision(
        "save",
        expected_state_version=0,
        idempotency_key="save-1",
        ingredient_additions=["mushroom"],
    )

    first_result = workflow.submit_impasse_decision("thread-1", decision)
    duplicate_result = workflow.submit_impasse_decision("thread-1", decision)

    assert duplicate_result == first_result
    assert duplicate_result["state_version"] == 1
    assert calls == {"chef": 2, "subchef": 2}


def test_concurrent_updates_from_same_version_allow_only_one(monkeypatch):
    workflow, _ = create_in_memory_workflow(
        monkeypatch,
        ["rejected", "rejected"],
    )
    workflow.start(
        create_initial_state(
            "Make a coxinha.",
            "thread-1",
            max_revisions=2,
        )
    )
    decisions = [
        create_decision(
            "save",
            expected_state_version=0,
            idempotency_key=f"save-{index}",
            ingredient_additions=[f"ingredient-{index}"],
        )
        for index in range(2)
    ]

    def submit(decision):
        try:
            return workflow.submit_impasse_decision("thread-1", decision)
        except StateVersionConflict as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, decisions))

    assert sum(isinstance(result, StateVersionConflict) for result in results) == 1
    state = workflow.get_state("thread-1")
    assert state["state_version"] == 1
    assert len(state["ingredient_additions"]) == 1


def test_idempotency_key_cannot_be_reused_with_different_payload(monkeypatch):
    workflow, _ = create_in_memory_workflow(
        monkeypatch,
        ["rejected", "rejected"],
    )
    workflow.start(
        create_initial_state(
            "Make a coxinha.",
            "thread-1",
            max_revisions=2,
        )
    )
    workflow.submit_impasse_decision(
        "thread-1",
        create_decision(
            "save",
            expected_state_version=0,
            idempotency_key="save-1",
            ingredient_additions=["mushroom"],
        ),
    )

    with pytest.raises(ValueError, match="cannot be reused"):
        workflow.submit_impasse_decision(
            "thread-1",
            create_decision(
                "save",
                expected_state_version=0,
                idempotency_key="save-1",
                ingredient_additions=["pepper"],
            ),
        )


def test_start_rejects_reuse_of_existing_thread_id(monkeypatch):
    workflow, _ = create_in_memory_workflow(
        monkeypatch,
        ["approved"],
    )
    initial_state = create_initial_state("Make a coxinha.", "thread-1")
    workflow.start(initial_state)

    with pytest.raises(ValueError, match="already exists"):
        workflow.start(initial_state)
