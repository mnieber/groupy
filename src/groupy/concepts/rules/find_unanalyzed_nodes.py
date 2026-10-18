import typing as T
from pathlib import Path

from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def find_unanalyzed_nodes(source_root: Path, module_names: T.List[str]) -> T.List[str]:
    # A function or class node is analyzed when its extract_method_priority is set
    result = []
    for module_name in module_names:
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        for located_node in get_located_nodes(module_node):
            node = located_node.node
            if (
                isinstance(node, (FunctionNode, ClassNode))
                and node.extract_method_priority is None
            ):
                result.append(f"{module_name}:{located_node.location}")
    return sorted(result)
