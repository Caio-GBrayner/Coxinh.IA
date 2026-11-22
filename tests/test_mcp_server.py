import asyncio

from fastmcp import Client
import pytest

from mcp_server.images import (
    ImageProviderError,
    ImageService,
    ProviderImage,
    SimulatedImageProvider,
)
from mcp_server.server import create_server
from src.graph.workflow import InMemoryWorkflow
from src.mcp_client import McpToolClient, McpToolError
from src.schemas import Recipe


IMAGE_PROMPT = "Coxinha dourada com recheio de frango."


def create_recipe() -> Recipe:
    return Recipe(
        dough="Potato dough",
        filling="Chicken",
        ingredients=["potato", "chicken"],
        preparation="Boil the potatoes and shape the dough.",
        utensils=["pot"],
        preparation_methods=["boiling"],
    )


def recipe_payload() -> dict:
    return create_recipe().model_dump(mode="json")


def full_server(**overrides):
    options = {
        "image_service": ImageService(SimulatedImageProvider()),
        "web_search": lambda query: [],
        "workflow": InMemoryWorkflow(),
    }
    options.update(overrides)
    return create_server(**options)


def call(server, name, arguments):
    return McpToolClient(server).call(name, arguments)


def list_tools(server):
    async def run():
        async with Client(server) as client:
            return {tool.name: tool for tool in await client.list_tools()}

    return asyncio.run(run())


class RaisingProvider:
    name = "raising"

    def __init__(self, error: Exception) -> None:
        self._error = error

    def generate(self, request: str, *, idempotency_key: str) -> ProviderImage:
        raise self._error


def test_bare_server_exposes_only_the_validation_tool():
    assert set(list_tools(create_server())) == {"validate_recipe_resources"}


def test_full_server_exposes_the_four_tools():
    assert set(list_tools(full_server())) == {
        "validate_recipe_resources",
        "generate_coxinha_image",
        "search_web",
        "record_impasse_decision",
    }


def test_tool_schemas_follow_the_contract():
    tools = list_tools(full_server())

    validation = tools["validate_recipe_resources"].input_schema
    assert set(validation["required"]) == {
        "recipe",
        "authorized_ingredients",
        "authorized_utensils",
        "authorized_preparation_methods",
    }
    assert set(tools["record_impasse_decision"].input_schema["required"]) == {
        "thread_id",
        "action",
        "expected_state_version",
        "idempotency_key",
    }
    assert set(tools["generate_coxinha_image"].input_schema["required"]) == {
        "recipe",
        "image_prompt",
    }
    assert tools["search_web"].input_schema["required"] == ["query"]


def validation_arguments(**overrides) -> dict:
    arguments = {
        "recipe": recipe_payload(),
        "authorized_ingredients": ["potato", "chicken"],
        "authorized_utensils": ["pot"],
        "authorized_preparation_methods": ["boiling"],
    }
    arguments.update(overrides)
    return arguments


def test_validation_passes_for_authorized_resources():
    result = call(
        create_server(), "validate_recipe_resources", validation_arguments()
    )

    assert result["status"] == "passed"
    assert result["unauthorized_ingredients"] == []
    assert result["unchecked_categories"] == []


def test_validation_rejects_unauthorized_resources():
    result = call(
        create_server(),
        "validate_recipe_resources",
        validation_arguments(authorized_ingredients=["potato"]),
    )

    assert result["status"] == "rejected"
    assert result["unauthorized_ingredients"] == ["chicken"]


def test_validation_is_incomplete_when_a_category_is_not_informed():
    result = call(
        create_server(),
        "validate_recipe_resources",
        validation_arguments(
            authorized_ingredients=None,
            authorized_utensils=None,
            authorized_preparation_methods=None,
        ),
    )

    assert result["status"] == "incomplete"
    assert set(result["unchecked_categories"]) == {
        "ingredients",
        "utensils",
        "preparation_methods",
    }


def test_validation_requires_added_ingredients_to_appear_in_the_recipe():
    result = call(
        create_server(),
        "validate_recipe_resources",
        validation_arguments(ingredient_additions=["cheese"]),
    )

    assert result["status"] == "rejected"
    assert result["missing_ingredient_additions"] == ["cheese"]


def test_validation_maps_blank_resources_to_invalid_input():
    with pytest.raises(McpToolError) as error:
        call(
            create_server(),
            "validate_recipe_resources",
            validation_arguments(authorized_ingredients=[" "]),
        )

    assert error.value.code == "invalid_input"


def test_validation_maps_schema_errors_to_invalid_input():
    arguments = validation_arguments()
    del arguments["recipe"]["dough"]

    with pytest.raises(McpToolError) as error:
        call(create_server(), "validate_recipe_resources", arguments)

    assert error.value.code == "invalid_input"


def image_arguments(**overrides) -> dict:
    arguments = {"recipe": recipe_payload(), "image_prompt": IMAGE_PROMPT}
    arguments.update(overrides)
    return arguments


def test_image_tool_generates_then_reuses_the_result():
    server = full_server()

    first = call(server, "generate_coxinha_image", image_arguments())
    second = call(server, "generate_coxinha_image", image_arguments())

    assert first["status"] == "generated"
    assert second["status"] == "reused"
    assert second["image_reference"] == first["image_reference"]
    assert second["idempotency_key"] == first["idempotency_key"]
    assert first["image_reference"].startswith("simulated://")


def test_image_tool_rejects_a_blank_description():
    with pytest.raises(McpToolError) as error:
        call(full_server(), "generate_coxinha_image", image_arguments(image_prompt=" "))

    assert error.value.code == "invalid_input"


def test_image_tool_maps_provider_failure_to_provider_unavailable():
    server = create_server(
        image_service=ImageService(RaisingProvider(ImageProviderError("down")))
    )

    with pytest.raises(McpToolError) as error:
        call(server, "generate_coxinha_image", image_arguments())

    assert error.value.code == "provider_unavailable"


def test_unexpected_errors_are_masked():
    server = create_server(
        image_service=ImageService(RaisingProvider(RuntimeError("segredo-interno")))
    )

    with pytest.raises(McpToolError) as error:
        call(server, "generate_coxinha_image", image_arguments())

    assert error.value.code == "tool_error"
    assert "segredo-interno" not in str(error.value)


def test_search_returns_results_with_title_url_and_content():
    results = [{"title": "Fonte A", "url": "https://example.test/a", "content": "trecho"}]
    server = create_server(web_search=lambda query: results)

    response = call(server, "search_web", {"query": "massa de batata"})

    assert response == {"status": "ok", "results": results}


def test_search_without_results_is_not_an_error():
    server = create_server(web_search=lambda query: [])

    response = call(server, "search_web", {"query": "massa de batata"})

    assert response == {"status": "no_results", "results": []}


def test_search_failure_is_provider_unavailable_and_does_not_leak():
    def failing_search(query):
        raise RuntimeError("chave-secreta")

    server = create_server(web_search=failing_search)

    with pytest.raises(McpToolError) as error:
        call(server, "search_web", {"query": "massa de batata"})

    assert error.value.code == "provider_unavailable"
    assert "chave-secreta" not in str(error.value)


def test_search_rejects_a_blank_query():
    server = create_server(web_search=lambda query: [])

    with pytest.raises(McpToolError) as error:
        call(server, "search_web", {"query": "  "})

    assert error.value.code == "invalid_input"


def test_search_result_without_url_is_provider_unavailable():
    server = create_server(web_search=lambda query: [{"title": "Sem URL", "content": "x"}])

    with pytest.raises(McpToolError) as error:
        call(server, "search_web", {"query": "massa de batata"})

    assert error.value.code == "provider_unavailable"
