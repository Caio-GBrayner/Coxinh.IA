from typing import Literal
import unicodedata

from pydantic import BaseModel

from src.schemas import Recipe
from src.utils.ingredients import mentions, split_items


ResourceCategory = Literal[
    "ingredients",
    "utensils",
    "preparation_methods",
]


class ResourceValidationResult(BaseModel):
    status: Literal["passed", "rejected", "incomplete"]
    unauthorized_ingredients: list[str]
    unauthorized_utensils: list[str]
    unauthorized_preparation_methods: list[str]
    missing_ingredient_additions: list[str]
    unchecked_categories: list[ResourceCategory]


def _normalize_resource(resource: str) -> str:
    if not isinstance(resource, str) or not resource.strip():
        raise ValueError("Resources must be non-empty strings.")

    normalized = unicodedata.normalize("NFKC", resource)
    return " ".join(normalized.split()).casefold()


def _find_unauthorized(
    used_resources: list[str],
    authorized_resources: list[str] | None,
    *,
    additional_authorizations: list[str] | None = None,
) -> list[str]:
    if authorized_resources is None:
        return []

    authorized = {_normalize_resource(item) for item in authorized_resources}
    if additional_authorizations:
        authorized.update(_normalize_resource(item) for item in additional_authorizations)

    return [
        item
        for item in used_resources
        if _normalize_resource(item) not in authorized
    ]


def validate_recipe_resources(
    recipe: Recipe,
    *,
    authorized_ingredients: list[str] | None,
    authorized_utensils: list[str] | None,
    authorized_preparation_methods: list[str] | None,
    ingredient_additions: list[str] | None = None,
) -> ResourceValidationResult:
    unchecked_categories: list[ResourceCategory] = []
    categories: tuple[tuple[ResourceCategory, list[str] | None], ...] = (
        ("ingredients", authorized_ingredients),
        ("utensils", authorized_utensils),
        ("preparation_methods", authorized_preparation_methods),
    )
    for category, authorized in categories:
        if authorized is None:
            unchecked_categories.append(category)

    unauthorized_ingredients = _find_unauthorized(
        recipe.ingredients,
        authorized_ingredients,
        additional_authorizations=split_items(ingredient_additions),
    )
    unauthorized_utensils = _find_unauthorized(
        recipe.utensils,
        authorized_utensils,
    )
    unauthorized_preparation_methods = _find_unauthorized(
        recipe.preparation_methods,
        authorized_preparation_methods,
    )

    # Tolerante de propósito: um item pedido no Impasse conta como usado se aparecer
    # em qualquer lista da receita, sem depender de acento, maiúsculas ou do nome
    # completo ("pao" casa com "pão francês"; "fogão" pode estar em utensílios).
    # Uma regra rígida aqui prendia a conversa no Impasse sem saída.
    used_resources = [
        *recipe.ingredients,
        *recipe.utensils,
        *recipe.preparation_methods,
    ]
    # split_items também corrige adições antigas gravadas juntas ("queijo, carne").
    missing_ingredient_additions = [
        item
        for item in split_items(ingredient_additions)
        if not any(mentions(item, used) for used in used_resources)
    ]

    has_violations = any(
        (
            unauthorized_ingredients,
            unauthorized_utensils,
            unauthorized_preparation_methods,
            missing_ingredient_additions,
        )
    )
    if has_violations:
        status: Literal["passed", "rejected", "incomplete"] = "rejected"
    elif unchecked_categories:
        status = "incomplete"
    else:
        status = "passed"

    return ResourceValidationResult(
        status=status,
        unauthorized_ingredients=unauthorized_ingredients,
        unauthorized_utensils=unauthorized_utensils,
        unauthorized_preparation_methods=unauthorized_preparation_methods,
        missing_ingredient_additions=missing_ingredient_additions,
        unchecked_categories=unchecked_categories,
    )
