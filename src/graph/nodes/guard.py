from typing import Literal

from src.graph.guardrail import GuardResult, check_text
from src.state import RecipeState


def guard_node(state: RecipeState) -> dict[str, object]:
    """Valida o pedido antes do Chef. Um pedido recusado encerra a execução."""
    result = check_text(state["raw_input"], "request")
    updates: dict[str, object] = {"guardrail": result.model_dump(mode="json")}
    if not result.allowed:
        updates["status"] = "blocked"
    return updates


def route_after_guard(state: RecipeState) -> Literal["chef", "end"]:
    """Só um resultado que libera explicitamente segue para o Chef."""
    stored = state.get("guardrail")
    if stored is None or not GuardResult.model_validate(stored).allowed:
        return "end"
    return "chef"
