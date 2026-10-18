from pathlib import Path

from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def load_or_create_module_node(source_root: Path, module_name: str) -> ModuleNode:
    node_file_path = get_module_node_file_path(source_root, module_name)
    if node_file_path.exists():
        return load_module_node(node_file_path)
    return ModuleNode(name=module_name)
