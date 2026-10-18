from pathlib import Path

from groupy.nodes.actions.insert_node_in_source_order import insert_node_in_source_order
from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.rules.find_located_node import find_located_node
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.nodes.rules.load_or_create_module_node import load_or_create_module_node


def move_node_to_module(
    source_root: Path, module_name: str, location: str, target_module_name: str
) -> None:
    # Moves the node (with its helper function nodes or method nodes) to the node
    # file of the target module. It keeps its analysis, and its move_to_file is
    # cleared.
    node_file_path = get_module_node_file_path(source_root, module_name)
    module_node = load_module_node(node_file_path)
    located_node = find_located_node(module_node, location)
    located_node.siblings.remove(located_node.node)
    save_module_node(module_node, node_file_path)

    node = located_node.node
    node.move_to_file = None
    target_module_node = load_or_create_module_node(source_root, target_module_name)
    insert_node_in_source_order(source_root, target_module_node, node)
    save_module_node(
        target_module_node,
        get_module_node_file_path(source_root, target_module_name),
    )
