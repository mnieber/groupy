import typing as T
from pathlib import Path

from groupy.call_graph.models.call_graph import CallGraph
from groupy.functions.rules.is_helper_candidate import is_helper_candidate
from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.get_source_qualified_name import get_source_qualified_name
from groupy.nodes.rules.load_module_node import load_module_node


def mark_helper_candidates(
    source_root: Path, call_graph: CallGraph, module_names: T.List[str]
) -> None:
    for module_name in module_names:
        node_file_path = get_module_node_file_path(source_root, module_name)
        module_node = load_module_node(node_file_path)
        for located_node in get_located_nodes(module_node):
            if isinstance(located_node.node, FunctionNode):
                location = f"{module_name}:{get_source_qualified_name(located_node)}"
                located_node.node.is_helper_candidate = is_helper_candidate(
                    call_graph, location
                )
        save_module_node(module_node, node_file_path)
