import typing as T
from pathlib import Path

from groupy.groups.actions.add_file_to_group import add_file_to_group
from groupy.groups.actions.remove_file_from_group import remove_file_from_group
from groupy.nodes.actions.create_module_node_file import create_module_node_file
from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.actions.sync_module_node import sync_module_node
from groupy.nodes.actions.sync_package_node_files import sync_package_node_files
from groupy.nodes.rules.get_module_names import get_module_names
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.get_module_node_from_source import get_module_node_from_source
from groupy.nodes.rules.get_target_module_names import get_target_module_names
from groupy.nodes.rules.load_module_node import load_module_node


def sync_node_files(source_root: Path, group_file_path: Path) -> T.List[str]:
    # Updates the node files so that their structure reflects the source again.
    # Returns a line per change, sorted by module and location.
    changes: T.List[T.Tuple[str, str, str]] = []
    module_names = get_module_names(source_root)
    target_module_names = get_target_module_names(source_root)

    for module_name in target_module_names:
        if module_name not in module_names:
            create_module_node_file(source_root, module_name)
            add_file_to_group(group_file_path, module_name)
            changes.append((module_name, "", "created the node file"))
            continue

        node_file_path = get_module_node_file_path(source_root, module_name)
        module_node = load_module_node(node_file_path)
        source_module_node = get_module_node_from_source(source_root, module_name)
        for location, description in sync_module_node(module_node, source_module_node):
            changes.append((module_name, location, description))
        save_module_node(module_node, node_file_path)

    for module_name in module_names:
        if module_name not in target_module_names:
            get_module_node_file_path(source_root, module_name).unlink()
            remove_file_from_group(group_file_path, module_name)
            changes.append((module_name, "", "deleted the node file"))

    sync_package_node_files(source_root)
    return [
        f"{module_name}: {description}"
        for module_name, _, description in sorted(changes, key=lambda c: c[:2])
    ]
