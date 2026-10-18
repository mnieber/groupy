import typing as T
from pathlib import Path

from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def get_line_count_by_module_name(
    source_root: Path, module_names: T.List[str]
) -> T.Dict[str, int]:
    return {
        module_name: load_module_node(
            get_module_node_file_path(source_root, module_name)
        ).line_count
        for module_name in module_names
    }
