import pytest

from src.graph import builder as graph_module
from src.graph.workflow import InMemoryWorkflow
from src.state import create_initial_state
from test_checkpoint import create_decision, create_in_memory_workflow


def test_retry_resume_after_chef_timeout(monkeypatch, stub_cook_llm):
    """Verifica que a retomada após timeout conclui sem reaplicar a decisão."""
    _, calls = create_in_memory_workflow(
        monkeypatch, ["rejected", "rejected", "approved"]
    )
    fake_chef = graph_module.chef_node
    timed_out = False

    def chef_with_timeout(state):
        """Simula um único timeout no Chef depois de sair do Impasse."""
        nonlocal timed_out
        if state["recipe_version"] == 2 and not timed_out:
            timed_out = True
            raise TimeoutError("Temporary provider failure")
        return fake_chef(state)

    monkeypatch.setattr(graph_module, "chef_node", chef_with_timeout)

    workflow = InMemoryWorkflow()
    workflow.start(create_initial_state("Make a coxinha.", "thread-1"))
    decision = create_decision(
        "resume",
        expected_state_version=0,
        idempotency_key="resume-1",
        ingredient_additions=["mushroom"],
        user_guidance="Keep the filling savory.",
    )

    with pytest.raises(TimeoutError, match="Temporary provider failure"):
        workflow.submit_impasse_decision("thread-1", decision)

    checkpoint = workflow.get_state("thread-1")
    assert checkpoint["status"] == "in_revision"
    assert checkpoint["state_version"] == 1
    assert checkpoint["total_attempts"] == 2
    stub_cook_llm.assert_not_called()

    result = workflow.submit_impasse_decision("thread-1", decision)

    assert result["status"] == "completed"
    assert result["state_version"] == 1
    assert result["recipe_version"] == 3
    assert result["revision_count"] == 1
    assert result["total_attempts"] == 3
    assert result["ingredient_additions"] == ["mushroom"]
    assert result["user_guidance"] == "Keep the filling savory."
    assert result["final_response"]["recipe"]["ingredients"] == [
        "potato",
        "chicken",
        "mushroom",
    ]
    assert calls == {"chef": 3, "subchef": 3}
    stub_cook_llm.assert_called_once()