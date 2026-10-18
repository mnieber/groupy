import typing as T
from pathlib import Path

from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def find_extract_method_candidates(
    source_root: Path, module_names: T.List[str]
) -> T.List[str]:
    # The function nodes with a high or medium priority, the high ones first
    candidates = []
    for module_name in module_names:
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        for located_node in get_located_nodes(module_node):
            node = located_node.node
            if isinstance(node, FunctionNode) and node.extract_method_priority in (
                "high",
                "medium",
            ):
                rank = 0 if node.extract_method_priority == "high" else 1
                candidates.append((rank, f"{module_name}:{located_node.location}"))
    return [location for _, location in sorted(candidates)]
