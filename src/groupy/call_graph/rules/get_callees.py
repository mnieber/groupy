import typing as T

from groupy.call_graph.models.call_edge import CallEdge
from groupy.call_graph.models.call_graph import CallGraph
from groupy.call_graph.rules.check_function_exists import check_function_exists


def get_callees(call_graph: CallGraph, location: str) -> T.List[CallEdge]:
    check_function_exists(call_graph, location)
    return [edge for edge in call_graph.edges if edge.caller == location]
