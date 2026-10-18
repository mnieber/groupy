from pathlib import Path

from dataclassy import values
from groupy.nodes.actions.insert_node_in_source_order import (
    insert_node_in_source_order,
)
from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.find_located_node import find_located_node
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.nodes.rules.load_or_create_module_node import load_or_create_module_node


def record_delegation(
    source_root: Path,
    module_name: str,
    method_location: str,
    function_name: str,
    target_module_name: str,
) -> None:
    # The new function gets the analysis of the method. The method node stays in
    # its class, with only the responsibility to delegate.
    node_file_path = get_module_node_file_path(source_root, module_name)
    module_node = load_module_node(node_file_path)
    located_node = find_located_node(module_node, method_location)
    method_node = located_node.node

    fields = values(method_node)
    fields.update(name=function_name, move_to_file=None, rename_to=None)
    function_node = FunctionNode(**fields)
    index = located_node.siblings.index(method_node)
    located_node.siblings[index] = FunctionNode(
        name=method_node.name, responsibilities=[f"Delegates to {function_name}"]
    )
    save_module_node(module_node, node_file_path)

    target_module_node = load_or_create_module_node(source_root, target_module_name)
    insert_node_in_source_order(source_root, target_module_node, function_node)
    save_module_node(
        target_module_node,
        get_module_node_file_path(source_root, target_module_name),
    )
