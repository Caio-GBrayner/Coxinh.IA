import pytest

from src.graph.resource_validation import validate_recipe_resources
from src.schemas import Recipe


def create_recipe(**overrides):
    data = {
        "dough": "Potato dough",
        "filling": "Chicken",
        "ingredients": ["potato", "chicken"],
        "preparation": "Boil the potatoes and shape the dough.",
        "utensils": ["pot"],
        "preparation_methods": ["boiling"],
    }
    data.update(overrides)
    return Recipe(**data)


def test_authorized_resources_match_case_and_whitespace_insensitively():
    result = validate_recipe_resources(
        create_recipe(),
        authorized_ingredients=[" POTATO ", "Chicken"],
        authorized_utensils=["POT"],
        authorized_preparation_methods=["Boiling"],
    )

    assert result.status == "passed"
    assert result.unchecked_categories == []


def test_unauthorized_resources_are_reported_by_category():
    result = validate_recipe_resources(
        create_recipe(),
        authorized_ingredients=["potato"],
        authorized_utensils=[],
        authorized_preparation_methods=["boiling"],
    )

    assert result.status == "rejected"
    assert result.unauthorized_ingredients == ["chicken"]
    assert result.unauthorized_utensils == ["pot"]


def test_user_added_ingredients_are_allowed_and_must_be_used():
    recipe = create_recipe(ingredients=["potato", "chicken", "cheese"])
    result = validate_recipe_resources(
        recipe,
        authorized_ingredients=["potato", "chicken"],
        authorized_utensils=["pot"],
        authorized_preparation_methods=["boiling"],
        ingredient_additions=[" Cheese "],
    )

    assert result.status == "passed"
    assert result.missing_ingredient_additions == []


def test_missing_user_added_ingredient_is_a_violation():
    result = validate_recipe_resources(
        create_recipe(),
        authorized_ingredients=["potato", "chicken"],
        authorized_utensils=["pot"],
        authorized_preparation_methods=["boiling"],
        ingredient_additions=["cheese"],
    )

    assert result.status == "rejected"
    assert result.missing_ingredient_additions == ["cheese"]


def test_missing_authorization_is_reported_as_incomplete():
    result = validate_recipe_resources(
        create_recipe(),
        authorized_ingredients=None,
        authorized_utensils=None,
        authorized_preparation_methods=None,
    )

    assert result.status == "incomplete"
    assert result.unchecked_categories == [
        "ingredients",
        "utensils",
        "preparation_methods",
    ]


def test_empty_authorization_means_no_resources_are_allowed():
    result = validate_recipe_resources(
        create_recipe(),
        authorized_ingredients=[],
        authorized_utensils=[],
        authorized_preparation_methods=[],
    )

    assert result.status == "rejected"
    assert result.unchecked_categories == []


def test_blank_authorized_resource_is_rejected():
    with pytest.raises(ValueError, match="non-empty strings"):
        validate_recipe_resources(
            create_recipe(),
            authorized_ingredients=[" "],
            authorized_utensils=["pot"],
            authorized_preparation_methods=["boiling"],
        )
