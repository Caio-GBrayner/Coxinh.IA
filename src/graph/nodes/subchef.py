from typing import Any

from pydantic import BaseModel

from src.graph.prompts.subchef import SUBCHEF_PROMPT
from src.graph.resource_validation import (
    ResourceValidationResult,
    validate_recipe_resources,
)
from src.schemas import Recipe, SubChefEvaluation
from src.state import RecipeState
from src.utils.llm_adapter import call_llm


class SubChefInput(BaseModel):
    recipe: Recipe
    authorized_ingredients: list[str] | None
    authorized_utensils: list[str] | None
    authorized_preparation_methods: list[str] | None
    ingredient_additions: list[str]


class SubChefContext(SubChefInput):
    resource_validation: ResourceValidationResult


SUBCHEF_TEMPERATURE = 0.1


def _resource_violations(
    result: ResourceValidationResult,
) -> list[str]:
    violations: list[str] = []
    for label, resources in (
        ("Unauthorized ingredients", result.unauthorized_ingredients),
        ("Unauthorized utensils", result.unauthorized_utensils),
        (
            "Unauthorized preparation methods",
            result.unauthorized_preparation_methods,
        ),
        ("Missing user-added ingredients", result.missing_ingredient_additions),
    ):
        if resources:
            violations.append(f"{label}: {', '.join(resources)}")
    return violations


def subchef_node(state: RecipeState) -> dict[str, Any]:
    recipe_value = state.get("recipe")
    if recipe_value is None:
        raise ValueError("The SubChef requires a recipe to review.")
    recipe = Recipe.model_validate(recipe_value)

    review_input = SubChefInput(
        recipe=recipe,
        authorized_ingredients=state.get("authorized_ingredients"),
        authorized_utensils=state.get("authorized_utensils"),
        authorized_preparation_methods=state.get(
            "authorized_preparation_methods"
        ),
        ingredient_additions=state.get("ingredient_additions", []),
    )
    resource_validation = validate_recipe_resources(
        review_input.recipe,
        authorized_ingredients=review_input.authorized_ingredients,
        authorized_utensils=review_input.authorized_utensils,
        authorized_preparation_methods=review_input.authorized_preparation_methods,
        ingredient_additions=review_input.ingredient_additions,
    )
    context = SubChefContext(
        **review_input.model_dump(),
        resource_validation=resource_validation,
    )

    violations = _resource_violations(resource_validation)
    if violations:
        return {
            "subchef_evaluation": SubChefEvaluation(
                decision="rejected",
                critique="The proposal does not respect the authorized resources.",
                evidence=violations,
            )
        }

    structured_model = SUBCHEF_PROMPT | call_llm(
        SUBCHEF_TEMPERATURE
    ).with_structured_output(SubChefEvaluation)
    evaluation = SubChefEvaluation.model_validate(
        structured_model.invoke(
            {"context": context.model_dump_json(exclude_none=True)}
        )
    )

    if resource_validation.unchecked_categories:
        validation_notes = [
            f"Authorization list for {category.replace('_', ' ')} was not provided; "
            "this category was not verified."
            for category in resource_validation.unchecked_categories
        ]
        evaluation = evaluation.model_copy(
            update={"evidence": [*evaluation.evidence, *validation_notes]}
        )

    return {"subchef_evaluation": evaluation}
