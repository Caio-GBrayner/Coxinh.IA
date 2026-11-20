
from langgraph.graph import END, START, StateGraph

from src.graph.nodes.chef import chef_node
from src.graph.nodes.record_review import record_review_node
from src.graph.nodes.subchef import subchef_node
from src.graph.routing import route_after_subchef
from src.state import RecipeState


builder = StateGraph(RecipeState)

builder.add_node("chef", chef_node)
builder.add_node("subchef", subchef_node)
builder.add_node("record_review", record_review_node)

builder.add_edge(START, "chef")
builder.add_edge("chef", "subchef")
builder.add_edge("subchef", "record_review")

builder.add_conditional_edges(
    "record_review",
    route_after_subchef,
    {
        "chef": "chef",
        "cook": END,
        "impasse": END,
    },
)

graph = builder.compile()
