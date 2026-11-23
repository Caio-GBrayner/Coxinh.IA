from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.finalize import finalize_node
from src.graph.impasse import impasse_node, route_after_impasse
from src.graph.nodes.chef import chef_node
from src.graph.nodes.cook import cook_node
from src.graph.nodes.health import health_node
from src.graph.nodes.image import image_node
from src.graph.nodes.record_review import record_review_node
from src.graph.nodes.subchef import subchef_node
from src.graph.routing import route_after_subchef
from src.state import RecipeState, create_initial_state


def prepare_node(state: dict[str, Any]) -> dict[str, Any]:
    """Monta o estado inicial a partir da entrada simples (raw_input, thread_id)."""
    return create_initial_state(state["raw_input"], state["thread_id"])


def build_graph(
    *,
    checkpointer: BaseCheckpointSaver | None = None,
    input_schema: type | None = None,
    with_impasse: bool | None = None,
) -> CompiledStateGraph[RecipeState, Any, RecipeState, RecipeState]:
    """Monta o grafo de revisão e finalização da receita.

    Com `input_schema`, a entrada é reduzida (por exemplo `raw_input` e
    `thread_id`) e um nó `prepare` cria o estado inicial antes do Chef.

    `with_impasse` inclui o nó de Impasse. Por padrão ele existe quando há
    checkpointer. O Studio o pede sem checkpointer, porque a plataforma fornece a
    persistência e não aceita um checkpointer no grafo.
    """
    if with_impasse is None:
        with_impasse = checkpointer is not None

    builder = StateGraph(RecipeState, input_schema=input_schema)

    builder.add_node("chef", chef_node)
    builder.add_node("subchef", subchef_node)
    builder.add_node("record_review", record_review_node)
    builder.add_node("cook", cook_node)
    builder.add_node("health", health_node)
    builder.add_node("image", image_node)
    builder.add_node("finalize", finalize_node)

    if input_schema is None:
        builder.add_edge(START, "chef")
    else:
        builder.add_node("prepare", prepare_node)
        builder.add_edge(START, "prepare")
        builder.add_edge("prepare", "chef")
    builder.add_edge("chef", "subchef")
    builder.add_edge("subchef", "record_review")
    builder.add_edge("cook", "health")
    builder.add_edge("health", "image")
    builder.add_edge("image", "finalize")
    builder.add_edge("finalize", END)

    if with_impasse:
        builder.add_node("impasse", impasse_node)
        builder.add_conditional_edges(
            "impasse",
            route_after_impasse,
            {"chef": "chef", "impasse": "impasse", "cook": "cook", "end": END},
        )

    builder.add_conditional_edges(
        "record_review",
        route_after_subchef,
        {
            "chef": "chef",
            "cook": "cook",
            "impasse": "impasse" if with_impasse else END,
        },
    )

    return builder.compile(checkpointer=checkpointer)


graph = build_graph()