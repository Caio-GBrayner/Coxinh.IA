from typing import Any

from pydantic import BaseModel, Field

from src.graph.prompts.chef import CHEF_PROMPT
from src.schemas import NonEmptyText, Recipe, SubChefEvaluation
from src.state import RecipeState
from src.utils.ingredients import split_items
from src.utils.llm_adapter import call_llm, invoke_structured


class ChefContext(BaseModel):
    request: NonEmptyText
    user_preferences: dict[str, Any]
    authorized_ingredients: list[str] | None
    authorized_utensils: list[str] | None
    authorized_preparation_methods: list[str] | None
    ingredient_additions: list[str]
    user_guidance: str | None
    previous_recipe: Recipe | None
    previous_critique: str | None
    next_recipe_version: int = Field(ge=1, strict=True)


CHEF_TEMPERATURE = 0.8


def chef_node(state: RecipeState) -> dict[str, object]:
    previous_recipe_value = state.get("recipe")
    previous_recipe = (
        Recipe.model_validate(previous_recipe_value)
        if previous_recipe_value is not None
        else None
    )
    previous_evaluation_value = state.get("subchef_evaluation")
    previous_evaluation = (
        SubChefEvaluation.model_validate(previous_evaluation_value)
        if previous_evaluation_value is not None
        else None
    )

    context = ChefContext(
        request=state["raw_input"],
        user_preferences=state.get("user_preferences", {}),
        authorized_ingredients=state.get("authorized_ingredients"),
        authorized_utensils=state.get("authorized_utensils"),
        authorized_preparation_methods=state.get(
            "authorized_preparation_methods"
        ),
        ingredient_additions=split_items(state.get("ingredient_additions", [])),
        user_guidance=state.get("user_guidance"),
        previous_recipe=previous_recipe,
        previous_critique=(
            previous_evaluation.critique
            if previous_evaluation is not None
            and previous_evaluation.decision == "rejected"
            else None
        ),
        next_recipe_version=state["recipe_version"] + 1,
    )

    structured_model = CHEF_PROMPT | call_llm(
        CHEF_TEMPERATURE
    ).with_structured_output(Recipe)
    recipe = Recipe.model_validate(
        invoke_structured(
            structured_model,
            {"context": context.model_dump_json(exclude_none=True)},
        )
    )

    return {
        "recipe": recipe,
        "recipe_version": context.next_recipe_version,
    }
