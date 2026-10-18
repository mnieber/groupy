from pathlib import Path

from groupy.nodes.actions.save_package_node import save_package_node
from groupy.nodes.models.package_node import PackageNode
from groupy.nodes.rules.get_package_module_names import get_package_module_names
from groupy.nodes.rules.get_package_names import get_package_names
from groupy.nodes.rules.get_package_node_file_path import (
    get_package_node_file_path,
)
from groupy.nodes.rules.load_package_node import load_package_node


def sync_package_node_files(source_root: Path) -> None:
    # Creates the package node file of a new package, and updates the module names
    # of the package node files
    for package_name in get_package_names(source_root):
        node_file_path = get_package_node_file_path(source_root, package_name)
        package_node = (
            load_package_node(node_file_path)
            if node_file_path.exists()
            else PackageNode(name=package_name)
        )
        package_node.module_names = get_package_module_names(source_root, package_name)
        save_package_node(package_node, node_file_path)
