from collections.abc import Callable
from typing import Any

from src.schemas import Recipe


HealthSearch = Callable[[str], list[dict[str, Any]]]


def build_health_queries(recipe: Recipe) -> list[str]:
    """Monta três consultas sobre riscos da massa, do recheio e do preparo."""

    return [
        (
            f"Quais são os riscos e contraindicações da ingestão "
            f"dos componentes desta massa: {recipe.dough}?"
        ),
        (
            f"Quais são os riscos e contraindicações da ingestão "
            f"dos componentes deste recheio: {recipe.filling}?"
        ),
        (
            f"Quais são os riscos à saúde associados a este modo de preparo: "
            f"{recipe.preparation}?"
        ),
    ]


def simulated_health_search(query: str) -> list[dict[str, Any]]:
    """Simula uma pesquisa sem resultados para testes sem acesso à rede."""

    return []