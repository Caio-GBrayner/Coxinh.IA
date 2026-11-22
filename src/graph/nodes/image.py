import logging

from src.mcp_client import get_tool_client
from src.schemas import Recipe
from src.state import RecipeState


logger = logging.getLogger(__name__)


def image_node(state: RecipeState) -> dict[str, object]:
    """Gera a imagem da receita final pela ferramenta MCP.

    Falha de imagem nunca bloqueia a receita: o nó marca `image_status` como
    `failed` e o fluxo segue para a finalização.
    """
    recipe_value = state.get("recipe")
    if recipe_value is None:
        raise ValueError("O nó de imagem exige uma receita.")
    recipe = Recipe.model_validate(recipe_value)

    image_prompt = state.get("image_prompt")
    if not image_prompt:
        raise ValueError("O nó de imagem exige a descrição visual do Cozinheiro.")

    try:
        result = get_tool_client().call(
            "generate_coxinha_image",
            {
                "recipe": recipe.model_dump(mode="json"),
                "image_prompt": image_prompt,
            },
        )
    except Exception as exc:
        logger.warning("Image generation failed: %s", type(exc).__name__)
        return {"image_url": None, "image_status": "failed"}

    return {
        "image_url": result["image_reference"],
        "image_status": result["status"],
        "idempotency_key": result["idempotency_key"],
    }
