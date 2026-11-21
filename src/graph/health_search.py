from collections.abc import Callable
from typing import Any

from src.schemas import Recipe


HealthSearch = Callable[[str], list[dict[str, Any]]]


def build_health_queries(recipe: Recipe) -> list[str]:
    """Uma consulta para cada parte da receita: massa, recheio e preparo."""
    return [recipe.dough, recipe.filling, recipe.preparation]


def simulated_health_search(query: str) -> list[dict[str, Any]]:
    """Substituto da etapa 8. Não consulta fontes reais; a busca web entra na etapa 9."""
    return []
