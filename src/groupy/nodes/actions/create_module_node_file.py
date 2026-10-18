from pathlib import Path

from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.get_module_node_from_source import get_module_node_from_source


def create_module_node_file(source_root: Path, module_name: str) -> None:
    module_node = get_module_node_from_source(source_root, module_name)
    save_module_node(module_node, get_module_node_file_path(source_root, module_name))
