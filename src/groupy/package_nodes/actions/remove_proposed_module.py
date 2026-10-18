from pathlib import Path

from groupy.nodes.utils.checks import check_has_entry
from groupy.package_nodes.actions.save_package_node import save_package_node
from groupy.package_nodes.rules.get_package_node_file_path import (
    get_package_node_file_path,
)
from groupy.package_nodes.rules.load_package_node import load_package_node


def remove_proposed_module(source_root: Path, name: str) -> None:
    node_file_path = get_package_node_file_path(source_root, ".")
    package_node = load_package_node(node_file_path)
    check_has_entry(package_node.proposed_modules, name, "proposed modules")
    del package_node.proposed_modules[name]
    save_package_node(package_node, node_file_path)
