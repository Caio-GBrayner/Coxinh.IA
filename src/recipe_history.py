from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class SessionRecipeHistory:
    """Guarda as receitas concluídas de uma sessão em memória."""

    def __init__(self) -> None:
        """Cria um histórico vazio para a sessão."""
        self._recipes: dict[str, dict[str, Any]] = {}

    def save_completed(self, result: Mapping[str, object]) -> str:
        """Salva a resposta de uma execução concluída e devolve seu ID."""
        if result.get("status") != "completed":
            raise ValueError("Só é possível salvar receitas concluídas.")

        recipe_id = result.get("thread_id")
        if not isinstance(recipe_id, str) or not recipe_id.strip():
            raise ValueError("A execução precisa de um thread_id válido.")

        response = result.get("final_response")
        if not isinstance(response, dict) or not response:
            raise ValueError("A execução precisa de uma resposta final.")

        self._recipes[recipe_id] = deepcopy(response)
        return recipe_id

    def list_recipes(self) -> list[dict[str, Any]]:
        """Lista as receitas da sessão, identificadas pelo ID."""
        return [
            {"id": recipe_id, **deepcopy(response)}
            for recipe_id, response in self._recipes.items()
        ]

    def get_recipe(self, recipe_id: str) -> dict[str, Any] | None:
        """Busca uma receita pelo ID na sessão atual."""
        response = self._recipes.get(recipe_id)
        if response is None:
            return None

        return {"id": recipe_id, **deepcopy(response)}