from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.nodes.chef import chef_node
from src.graph.impasse import impasse_node, route_after_impasse
from src.graph.nodes.subchef import subchef_node
from src.graph.routing import record_subchef_evaluation, route_after_subchef
from src.state import RecipeState


def _record_subchef_evaluation_node(
    state: RecipeState,
) -> dict[str, object]:
    updated_state = record_subchef_evaluation(state)
    return {
        "revision_count": updated_state["revision_count"],
        "total_attempts": updated_state["total_attempts"],
        "status": updated_state["status"],
    }


def build_graph(
    *,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph[RecipeState, Any, RecipeState, RecipeState]:
    builder: StateGraph[RecipeState, Any, RecipeState, RecipeState] = StateGraph(
        RecipeState
    )
    builder.add_node("chef", chef_node)
    builder.add_node("subchef", subchef_node)
    builder.add_node("record_evaluation", _record_subchef_evaluation_node)
    builder.add_node("impasse", impasse_node)

    builder.add_edge(START, "chef")
    builder.add_edge("chef", "subchef")
    builder.add_edge("subchef", "record_evaluation")
    builder.add_conditional_edges(
        "record_evaluation",
        route_after_subchef,
        {
            "chef": "chef",
            "cook": END,
            "impasse": "impasse",
        },
    )
    builder.add_conditional_edges(
        "impasse",
        route_after_impasse,
        {
            "chef": "chef",
            "impasse": "impasse",
            "end": END,
        },
    )

    return builder.compile(checkpointer=checkpointer)
