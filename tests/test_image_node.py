import pytest

from src.graph.nodes import image
from src.mcp_client import McpToolError
from src.schemas import Recipe
from src.state import create_initial_state


IMAGE_PROMPT = "Coxinha dourada com recheio de frango."


class FakeToolClient:
    def __init__(self, result=None, error=None) -> None:
        self.calls = []
        self._result = result
        self._error = error

    def call(self, name, arguments):
        self.calls.append((name, arguments))
        if self._error is not None:
            raise self._error
        return self._result


def create_recipe() -> Recipe:
    return Recipe(
        dough="Potato dough",
        filling="Chicken",
        ingredients=["potato", "chicken"],
        preparation="Boil the potatoes and shape the dough.",
        utensils=["pot"],
        preparation_methods=["boiling"],
    )


def create_state():
    state = create_initial_state("Make a coxinha.", "thread-1")
    state["recipe"] = create_recipe()
    state["image_prompt"] = IMAGE_PROMPT
    return state


def use_client(monkeypatch, client):
    monkeypatch.setattr(image, "get_tool_client", lambda: client)
    return client


def test_image_node_returns_the_generated_reference(monkeypatch):
    client = use_client(
        monkeypatch,
        FakeToolClient(
            {
                "status": "generated",
                "image_reference": "simulated://coxinha/abc",
                "idempotency_key": "key-abc",
                "provider_request_id": "req-1",
            }
        ),
    )

    result = image.image_node(create_state())

    assert result == {
        "image_url": "simulated://coxinha/abc",
        "image_status": "generated",
        "idempotency_key": "key-abc",
    }
    name, arguments = client.calls[0]
    assert name == "generate_coxinha_image"
    assert arguments["image_prompt"] == IMAGE_PROMPT
    assert arguments["recipe"]["filling"] == "Chicken"


def test_image_node_reports_a_reused_image(monkeypatch):
    use_client(
        monkeypatch,
        FakeToolClient(
            {
                "status": "reused",
                "image_reference": "simulated://coxinha/abc",
                "idempotency_key": "key-abc",
            }
        ),
    )

    assert image.image_node(create_state())["image_status"] == "reused"


def test_tool_error_marks_the_image_as_failed_without_raising(monkeypatch):
    use_client(
        monkeypatch,
        FakeToolClient(error=McpToolError("provider_unavailable", "down")),
    )

    result = image.image_node(create_state())

    assert result == {"image_url": None, "image_status": "failed"}


def test_any_failure_marks_the_image_as_failed(monkeypatch):
    use_client(monkeypatch, FakeToolClient(error=ConnectionError("no route")))

    result = image.image_node(create_state())

    assert result == {"image_url": None, "image_status": "failed"}


def test_image_node_does_not_touch_the_recipe_or_the_status(monkeypatch):
    use_client(monkeypatch, FakeToolClient(error=McpToolError("tool_error", "x")))
    state = create_state()
    original_recipe = state["recipe"]

    result = image.image_node(state)

    assert set(result) == {"image_url", "image_status"}
    assert state["recipe"] == original_recipe


def test_image_node_requires_a_recipe():
    state = create_initial_state("Make a coxinha.", "thread-1")
    state["image_prompt"] = IMAGE_PROMPT

    with pytest.raises(ValueError, match="exige uma receita"):
        image.image_node(state)


def test_image_node_requires_the_visual_description():
    state = create_state()
    state["image_prompt"] = None

    with pytest.raises(ValueError, match="descrição visual"):
        image.image_node(state)
