from pathlib import Path

from groupy.nodes.actions.save_package_node import save_package_node
from groupy.nodes.rules.get_package_node_file_path import (
    get_package_node_file_path,
)
from groupy.nodes.rules.load_package_node import load_package_node


def set_proposed_module(source_root: Path, name: str, description: str) -> None:
    # The proposed modules are recorded in the package node file of the target dir
    node_file_path = get_package_node_file_path(source_root, ".")
    package_node = load_package_node(node_file_path)
    package_node.proposed_modules[name] = description
    save_package_node(package_node, node_file_path)
