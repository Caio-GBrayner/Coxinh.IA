import pytest
from pydantic import ValidationError

from src.schemas import CookOutput


@pytest.fixture
def cook_output_data() -> dict[str, object]:
    """Monta uma saída válida do Cozinheiro para os testes."""
    return {
        "title": "Abóboríssima",
        "subtitle": "Coxinha de abóbora",
        "steps": ["Modele a massa.", "Asse no forno."],
        "image_prompt": "Uma coxinha dourada com recheio de abóbora.",
        "ingredients": ["abóbora"],
        "utensils": ["assadeira"],
        "preparation_methods": ["forno"],
    }


def test_cook_output_preserves_step_order(cook_output_data):
    """Verifica que uma saída válida mantém a ordem do preparo."""
    output = CookOutput.model_validate(cook_output_data)

    assert output.steps == ["Modele a massa.", "Asse no forno."]


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("subtitle", "   "),
        ("steps", []),
    ],
)
def test_cook_output_rejects_invalid_field(cook_output_data, field, invalid_value):
    """Verifica que o modelo rejeita subtítulo em branco ou falta de passos."""
    cook_output_data[field] = invalid_value

    with pytest.raises(ValidationError) as error:
        CookOutput.model_validate(cook_output_data)

    assert error.value.errors()[0]["loc"] == (field,)