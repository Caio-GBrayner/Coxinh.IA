from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from src.persistence.recipe_store import RecipeRepository


class SessionRecipeHistory:
    """Guarda as receitas concluídas, em memória ou em um banco.

    Sem `store`, cada instância tem o próprio histórico e ele some com o
    processo. Com `store`, as receitas sobrevivem a reinícios e todas as
    instâncias que usam o mesmo banco enxergam a mesma lista.
    A listagem segue a ordem de gravação, da mais antiga para a mais recente.
    """

    def __init__(self, store: RecipeRepository | None = None) -> None:
        """Cria um histórico vazio em memória ou ligado ao banco."""
        self._store = store
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

        if self._store is not None:
            self._store.save(recipe_id, deepcopy(response))
        else:
            self._recipes[recipe_id] = deepcopy(response)
        return recipe_id

    def list_recipes(self) -> list[dict[str, Any]]:
        """Lista as receitas, identificadas pelo ID, da mais antiga à mais recente."""
        if self._store is not None:
            return [
                {"id": recipe_id, **response}
                for recipe_id, response in self._store.list()
            ]
        return [
            {"id": recipe_id, **deepcopy(response)}
            for recipe_id, response in self._recipes.items()
        ]

    def get_recipe(self, recipe_id: str) -> dict[str, Any] | None:
        """Busca uma receita pelo ID."""
        if self._store is not None:
            response = self._store.get(recipe_id)
        else:
            response = deepcopy(self._recipes.get(recipe_id))
        if response is None:
            return None

        return {"id": recipe_id, **response}
