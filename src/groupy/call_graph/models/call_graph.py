import typing as T

from dataclassy import dataclass
from groupy.call_graph.models.call_edge import CallEdge


@dataclass
class CallGraph:
    # The locations of all functions and methods, also those without edges
    functions: T.List[str] = []
    edges: T.List[CallEdge] = []
