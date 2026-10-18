from pathlib import Path

import yaml
from groupy.call_graph.models.call_edge import CallEdge
from groupy.call_graph.models.call_graph import CallGraph


def load_call_graph(call_graph_path: Path) -> CallGraph:
    data = yaml.safe_load(call_graph_path.read_text()) or {}
    return CallGraph(
        functions=data.get("functions") or [],
        edges=[CallEdge(**item) for item in data.get("edges") or []],
    )
