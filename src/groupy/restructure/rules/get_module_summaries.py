import typing as T
from pathlib import Path

from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def get_module_summaries(
    source_root: Path, module_names: T.List[str]
) -> T.Dict[str, T.Dict[str, T.Any]]:
    # Per module node file: its concepts, and the first responsibility (or None) of
    # each top-level function and class
    summaries = {}
    for module_name in module_names:
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        nodes = [*module_node.class_nodes, *module_node.function_nodes]
        summaries[module_name] = {
            "concepts": dict(module_node.concepts),
            "code_units": {
                node.name: (node.responsibilities[0] if node.responsibilities else None)
                for node in nodes
            },
        }
    return summaries
