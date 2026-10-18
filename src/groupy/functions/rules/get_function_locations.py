import typing as T
from pathlib import Path

from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.get_source_qualified_name import get_source_qualified_name
from groupy.nodes.rules.load_module_node import load_module_node


def get_function_locations(
    source_root: Path, module_names: T.List[str]
) -> T.List[T.Tuple[str, str, FunctionNode]]:
    # Returns, per function node (also method and helper function nodes), its
    # location in the node file and in the source (both as <module>:<location>)
    result = []
    for module_name in module_names:
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        for located_node in get_located_nodes(module_node):
            if isinstance(located_node.node, FunctionNode):
                result.append(
                    (
                        f"{module_name}:{located_node.location}",
                        f"{module_name}:{get_source_qualified_name(located_node)}",
                        located_node.node,
                    )
                )
    return result
