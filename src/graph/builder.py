from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.impasse import impasse_node, route_after_impasse
from src.graph.nodes.chef import chef_node
from src.graph.nodes.record_review import record_review_node
from src.graph.nodes.subchef import subchef_node
from src.graph.routing import route_after_subchef
from src.state import RecipeState


def build_graph(
    *,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph[RecipeState, Any, RecipeState, RecipeState]:
    """Monta o grafo de revisão, com pausa no Impasse quando há checkpoint."""
    builder = StateGraph(RecipeState)

    builder.add_node("chef", chef_node)
    builder.add_node("subchef", subchef_node)
    builder.add_node("record_review", record_review_node)

    builder.add_edge(START, "chef")
    builder.add_edge("chef", "subchef")
    builder.add_edge("subchef", "record_review")

    if checkpointer is not None:
        builder.add_node("impasse", impasse_node)
        builder.add_conditional_edges(
            "impasse",
            route_after_impasse,
            {"chef": "chef", "impasse": "impasse", "end": END},
        )

    builder.add_conditional_edges(
        "record_review",
        route_after_subchef,
        {
            "chef": "chef",
            "cook": END,
            "impasse": "impasse" if checkpointer is not None else END,
        },
    )

    return builder.compile(checkpointer=checkpointer)


graph = build_graph()