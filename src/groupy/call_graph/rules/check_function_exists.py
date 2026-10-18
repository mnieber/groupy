from groupy.call_graph.models.call_graph import CallGraph
from groupy.nodes.utils.exceptions import NodeNotFoundError


def check_function_exists(call_graph: CallGraph, location: str) -> None:
    if location not in call_graph.functions:
        raise NodeNotFoundError(f"The call graph has no function {location}")
