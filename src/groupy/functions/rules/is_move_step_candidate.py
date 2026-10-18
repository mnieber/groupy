from groupy.call_graph.models.call_graph import CallGraph


def is_move_step_candidate(call_graph: CallGraph, location: str) -> bool:
    # A function is a candidate when it has at least one caller, and all its
    # callers are functions or methods that call it through a certain edge
    edges = [edge for edge in call_graph.edges if edge.callee == location]
    return bool(edges) and all(
        edge.is_certain and not edge.caller.endswith(":@module") for edge in edges
    )
