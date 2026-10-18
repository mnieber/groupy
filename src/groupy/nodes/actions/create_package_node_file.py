from pathlib import Path

from groupy.nodes.actions.save_package_node import save_package_node
from groupy.nodes.models.package_node import PackageNode
from groupy.nodes.rules.get_package_module_names import get_package_module_names
from groupy.nodes.rules.get_package_node_file_path import get_package_node_file_path


def create_package_node_file(source_root: Path, package_name: str) -> None:
    package_node = PackageNode(
        name=package_name,
        module_names=get_package_module_names(source_root, package_name),
    )
    save_package_node(
        package_node, get_package_node_file_path(source_root, package_name)
    )
