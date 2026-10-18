import typing as T
from pathlib import Path

from groupy.call_graph.enums import CallScopes
from groupy.call_graph.models.call_edge import CallEdge
from groupy.call_graph.models.call_graph import CallGraph
from groupy.call_graph.models.call_graph_view import (
    CallGraphView,
    CallView,
    FunctionView,
)
from groupy.nodes.rules.find_node import find_node
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.nodes.utils.exceptions import AmbiguousLocationError, NodeNotFoundError


def get_call_graph_view(
    call_graph: CallGraph,
    source_root: Path,
    chunk_module_names: T.List[str],
    max_callers: int = 10,
) -> CallGraphView:
    function_views = []
    for location in call_graph.functions:
        if _get_module_name(location) not in chunk_module_names:
            continue

        caller_edges = [edge for edge in call_graph.edges if edge.callee == location]
        callee_edges = [edge for edge in call_graph.edges if edge.caller == location]
        callers = _get_call_views(
            source_root, location, chunk_module_names, caller_edges, "caller"
        )
        callees = _get_call_views(
            source_root, location, chunk_module_names, callee_edges, "callee"
        )

        # Too many callers are summarized
        caller_summary = None
        if len(callers) > max_callers:
            nr_of_modules = len({edge.file for edge in caller_edges})
            caller_summary = (
                f"called from {len(caller_edges)} places in {nr_of_modules} modules"
            )
            callers = []

        function_views.append(
            FunctionView(
                location=location,
                callers=callers,
                callees=callees,
                caller_summary=caller_summary,
            )
        )
    return CallGraphView(function_views=function_views)


def _get_module_name(location: str) -> str:
    return location.split(":", 1)[0]


def _get_call_views(
    source_root: Path,
    location: str,
    chunk_module_names: T.List[str],
    edges: T.List[CallEdge],
    end: str,
) -> T.List[CallView]:
    # Each caller or callee is listed once, also when it is called several times
    is_certain_by_location: T.Dict[str, bool] = {}
    for edge in edges:
        other = getattr(edge, end)
        is_certain_by_location[other] = (
            is_certain_by_location.get(other, False) or edge.is_certain
        )

    call_views = []
    for other, is_certain in is_certain_by_location.items():
        other_module_name = _get_module_name(other)
        if other_module_name == _get_module_name(location):
            scope = CallScopes.SAME_MODULE
        elif other_module_name in chunk_module_names:
            scope = CallScopes.CHUNK
        else:
            scope = CallScopes.OUTSIDE_CHUNK

        # A function outside the chunk is described by its first responsibility
        responsibility = None
        if scope == CallScopes.OUTSIDE_CHUNK:
            responsibility = _get_first_responsibility(source_root, other)
        call_views.append(
            CallView(
                location=other,
                scope=scope,
                is_certain=is_certain,
                responsibility=responsibility,
            )
        )
    return call_views


def _get_first_responsibility(source_root: Path, location: str) -> T.Optional[str]:
    module_name, qualified_name = location.split(":", 1)
    node_file_path = get_module_node_file_path(source_root, module_name)
    if qualified_name == "@module" or not node_file_path.exists():
        return None
    try:
        node = find_node(load_module_node(node_file_path), qualified_name)
    except (NodeNotFoundError, AmbiguousLocationError):
        return None
    responsibilities = getattr(node, "responsibilities", [])
    return responsibilities[0] if responsibilities else None
