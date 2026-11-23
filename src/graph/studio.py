from typing import TypedDict

from src.graph.builder import build_graph


class StudioInput(TypedDict):
    raw_input: str
    thread_id: str


graph = build_graph(input_schema=StudioInput, with_impasse=True)
