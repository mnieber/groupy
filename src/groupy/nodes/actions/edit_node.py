import typing as T
from pathlib import Path

from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.rules.find_located_node_in_source import (
    find_located_node_in_source,
)
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def edit_node(
    source_root: Path,
    module_name: str,
    location: str,
    edit: T.Callable[[T.Any], None],
) -> None:
    # The edit raises an error before the node file is saved if it cannot be done
    node_file_path = get_module_node_file_path(source_root, module_name)
    module_node = load_module_node(node_file_path)
    edit(
        find_located_node_in_source(
            source_root, module_name, module_node, location
        ).node
    )
    save_module_node(module_node, node_file_path)
