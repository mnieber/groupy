from groupy.nodes.models.located_node import LocatedNode
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.utils.exceptions import AmbiguousLocationError, NodeNotFoundError


def find_located_node(module_node: ModuleNode, location: str) -> LocatedNode:
    located_nodes = get_located_nodes(module_node)

    # A location that is the full qualified name of a node finds that node
    for located_node in located_nodes:
        if located_node.location == location:
            return located_node

    # Otherwise, the location must match the end of exactly one qualified name
    matches = [
        located_node
        for located_node in located_nodes
        if located_node.location.endswith(f".{location}")
    ]
    if not matches:
        raise NodeNotFoundError(f"{module_node.name} has no node at {location}")
    if len(matches) > 1:
        locations = ", ".join(match.location for match in matches)
        raise AmbiguousLocationError(
            f"The location {location} in {module_node.name} matches {locations}"
        )
    return matches[0]
