from src.schemas import CookOutput, Recipe
from src.state import RecipeState


def finalize_node(state: RecipeState) -> dict[str, object]:
    """Monta a resposta final da receita e conclui a execução."""
    if state.get("status") != "approved":
        raise ValueError("A finalização exige uma proposta aprovada.")

    cook_output = state.get("cook_output")
    if cook_output is None:
        raise ValueError("A finalização exige a saída do Cozinheiro.")

    recipe = Recipe.model_validate(state["recipe"])
    presentation = CookOutput.model_validate(cook_output)

    final_response = {
        "recipe": {
            "title": presentation.title,
            "subtitle": presentation.subtitle,
            "dough": recipe.dough,
            "filling": recipe.filling,
            "ingredients": recipe.ingredients,
            "utensils": recipe.utensils,
            "preparation_methods": recipe.preparation_methods,
            "steps": presentation.steps,
            "image_prompt": presentation.image_prompt,
        },
        "health": {
            "warning": state.get("health_warning"),
            "contraindications": state.get("health_contraindications") or [],
            "sources": state.get("health_sources") or [],
            "uncertainty": state.get("health_uncertainty"),
            "health_status": state.get("health_status") or "pending",
        },
        "resource_validation": state.get(
            "cook_resource_validation", "incomplete"
        ),
    }

    return {"final_response": final_response, "status": "completed"}