import typing as T
from pathlib import Path

from groupy.call_graph.models.call_graph import CallGraph
from groupy.functions.rules.get_source import get_source


def get_caller_sources(
    source_root: Path, call_graph: CallGraph, locations: T.List[str]
) -> T.Dict[str, str]:
    # The source of each caller of the functions at the (source) locations, also
    # in other modules. The source of a method is dedented.
    caller_locations = sorted(
        {edge.caller for edge in call_graph.edges if edge.callee in locations}
    )
    return {
        caller_location: get_source(source_root, caller_location).rstrip("\n")
        for caller_location in caller_locations
        if not caller_location.endswith(":@module")
    }
