from pathlib import Path

from groupy.nodes.actions.create_module_node_file import create_module_node_file
from groupy.nodes.actions.create_package_node_file import create_package_node_file
from groupy.nodes.rules.get_package_names import get_package_names
from groupy.nodes.rules.get_target_module_names import get_target_module_names


def create_node_files(source_root: Path) -> None:
    for package_name in get_package_names(source_root):
        create_package_node_file(source_root, package_name)
    for module_name in get_target_module_names(source_root):
        create_module_node_file(source_root, module_name)
