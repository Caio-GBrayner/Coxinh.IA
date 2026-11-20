from src.graph.routing import record_subchef_evaluation
from src.state import RecipeState


def record_review_node(state: RecipeState) -> dict[str, object]:
    """Registra a avaliação do SubChef e devolve os contadores e o status atualizados."""
    updated_state = record_subchef_evaluation(state)

    return {
        "revision_count": updated_state["revision_count"],
        "total_attempts": updated_state["total_attempts"],
        "status": updated_state["status"],
    }
