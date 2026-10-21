from pathlib import Path

from groupy.nodes.models.located_node import LocatedNode
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.rules.find_located_node import find_located_node
from groupy.nodes.rules.get_embedded_function_locations import (
    get_embedded_function_locations,
)
from groupy.nodes.utils.exceptions import (
    EmbeddedFunctionNodeNotFoundError,
    NodeNotFoundError,
)


def find_located_node_in_source(
    source_root: Path, module_name: str, module_node: ModuleNode, location: str
) -> LocatedNode:
    # Like find_located_node, but a location of an embedded function (which has
    # no node) raises an error that says so, so that a callback is not retried
    try:
        return find_located_node(module_node, location)
    except NodeNotFoundError as error:
        for embedded_location in get_embedded_function_locations(
            source_root, module_name
        ):
            if embedded_location == location or embedded_location.endswith(
                f".{location}"
            ):
                parent_location = embedded_location.rpartition(".")[0]
                raise EmbeddedFunctionNodeNotFoundError(
                    f"{embedded_location} in {module_name} is a function that is "
                    f"embedded in {parent_location}. Embedded functions have no "
                    f"node: don't make callbacks for them, and don't retry. Make "
                    f"the callbacks for {parent_location} instead."
                ) from error
        raise
