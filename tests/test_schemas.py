import pytest
from pydantic import ValidationError

from src.schemas import Recipe, SubChefEvaluation


def valid_recipe_data():
    return {
        "dough": "Potato dough",
        "filling": "Chicken",
        "ingredients": ["potato", "chicken"],
        "preparation": "Shape the dough and add the filling.",
        "utensils": ["pot"],
        "preparation_methods": ["boiling"],
    }


def test_recipe_normalizes_required_text():
    data = valid_recipe_data()
    data["dough"] = "  Potato dough  "
    data["ingredients"] = [" potato ", " chicken "]

    recipe = Recipe(**data)

    assert recipe.dough == "Potato dough"
    assert recipe.ingredients == ["potato", "chicken"]
    assert recipe.revision_summary is None


@pytest.mark.parametrize(
    "field",
    [
        "dough",
        "filling",
        "ingredients",
        "preparation",
        "utensils",
        "preparation_methods",
    ],
)
def test_recipe_requires_structured_fields(field):
    data = valid_recipe_data()
    del data[field]

    with pytest.raises(ValidationError) as error:
        Recipe(**data)

    assert error.value.errors()[0]["loc"] == (field,)
    assert error.value.errors()[0]["type"] == "missing"


@pytest.mark.parametrize(
    "field, value",
    [
        ("dough", ""),
        ("dough", "   "),
        ("filling", ""),
        ("preparation", "   "),
        ("ingredients", []),
        ("ingredients", [""]),
        ("ingredients", ["potato", "   "]),
        ("utensils", [""]),
        ("preparation_methods", ["  "]),
        ("dough", 123),
        ("ingredients", "potato"),
        ("ingredients", [123]),
    ],
)
def test_recipe_rejects_invalid_values(field, value):
    data = valid_recipe_data()
    data[field] = value

    with pytest.raises(ValidationError) as error:
        Recipe(**data)

    assert error.value.errors()[0]["loc"][0] == field


def test_approved_evaluation_allows_empty_critique():
    evaluation = SubChefEvaluation(decision="approved", critique="")

    assert evaluation.decision == "approved"
    assert evaluation.critique == ""


def test_rejected_evaluation_requires_critique():
    with pytest.raises(ValidationError, match="must include a critique"):
        SubChefEvaluation(decision="rejected", critique="  ")


def test_evaluation_rejects_unknown_decision():
    with pytest.raises(ValidationError) as error:
        SubChefEvaluation.model_validate(
            {"decision": "maybe", "critique": "Still reviewing."}
        )

    assert error.value.errors()[0]["loc"] == ("decision",)
