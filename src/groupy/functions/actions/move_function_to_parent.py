from pathlib import Path

from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.find_located_node import find_located_node
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def move_function_to_parent(
    source_root: Path, module_name: str, function_location: str, parent_location: str
) -> None:
    node_file_path = get_module_node_file_path(source_root, module_name)
    module_node = load_module_node(node_file_path)
    located_function = find_located_node(module_node, function_location)
    parent = find_located_node(module_node, parent_location).node

    function_node = located_function.node
    if not isinstance(function_node, FunctionNode) or not isinstance(
        parent, FunctionNode
    ):
        raise InvalidParentError(
            f"Only a function can be moved to a function ({function_location} to "
            f"{parent_location})"
        )

    # A function cannot become a helper function of itself or of its own helpers
    if parent is function_node or _contains(function_node, parent):
        raise InvalidParentError(
            f"{parent_location} cannot be the parent of {function_location}"
        )

    located_function.siblings.remove(function_node)
    parent.helper_function_nodes.append(function_node)
    save_module_node(module_node, node_file_path)


def _contains(function_node: FunctionNode, node: FunctionNode) -> bool:
    return any(
        helper_function_node is node or _contains(helper_function_node, node)
        for helper_function_node in function_node.helper_function_nodes
    )


class InvalidParentError(Exception):
    pass
