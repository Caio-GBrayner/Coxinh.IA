import json

from src.graph.prompts.cook import COOK_PROMPT
from src.graph.resource_validation import validate_recipe_resources
from src.schemas import CookOutput, Recipe
from src.state import RecipeState
from src.utils.llm_adapter import call_llm


COOK_TEMPERATURE = 0.4
COOK_MAX_ATTEMPTS = 2


def cook_node(state: RecipeState) -> dict[str, object]:
    """Gera a apresentação da receita e confere os recursos declarados."""
    if state.get("status") != "approved":
        raise ValueError("O Cozinheiro precisa de uma proposta aprovada.")

    recipe = Recipe.model_validate(state["recipe"])
    authorization = validate_recipe_resources(
        recipe,
        authorized_ingredients=state.get("authorized_ingredients"),
        authorized_utensils=state.get("authorized_utensils"),
        authorized_preparation_methods=state.get(
            "authorized_preparation_methods"
        ),
        ingredient_additions=state.get("ingredient_additions", []),
    )
    if authorization.status == "rejected":
        raise ValueError("A proposta viola as autorizações do usuário.")

    approved_resources = {
        "ingredients": recipe.ingredients,
        "utensils": recipe.utensils,
        "preparation_methods": recipe.preparation_methods,
    }
    context = {"recipe": recipe.model_dump(mode="json")}

    model = call_llm(COOK_TEMPERATURE).with_structured_output(CookOutput)
    chain = COOK_PROMPT | model

    for _ in range(COOK_MAX_ATTEMPTS):
        output = CookOutput.model_validate(
            chain.invoke({"context": json.dumps(context, ensure_ascii=False)})
        )
        declared_resources = {
            "ingredients": output.ingredients,
            "utensils": output.utensils,
            "preparation_methods": output.preparation_methods,
        }
        mismatches = [
            field
            for field, approved in approved_resources.items()
            if set(declared_resources[field]) != set(approved)
        ]

        if not mismatches:
            return {
                "cook_output": output.model_dump(mode="json"),
                "recipe_steps": "\n".join(
                    f"{number}. {step}"
                    for number, step in enumerate(output.steps, start=1)
                ),
                "image_prompt": output.image_prompt,
                "cook_resource_validation": authorization.status,
            }

        context["resource_correction"] = (
            "Na tentativa anterior, estas listas divergiram da proposta: "
            f"{', '.join(mismatches)}. Copie todos os itens dessas listas "
            "da receita aprovada, preservando seus nomes."
        )

    raise ValueError(
        "Falha na finalização: o Cozinheiro divergiu dos recursos "
        f"da proposta aprovada nas listas: {', '.join(mismatches)}."
    )