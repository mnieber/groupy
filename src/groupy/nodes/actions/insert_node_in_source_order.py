import ast
import typing as T
from pathlib import Path

from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.module_node import ModuleNode
from groupy.renamings.rules.get_scope_symbols import get_scope_symbols


def insert_node_in_source_order(
    source_root: Path, module_node: ModuleNode, node: T.Any
) -> None:
    # Adds the node to the list of its kind, before the first node that follows it
    # in the source of the module
    if isinstance(node, FunctionNode):
        nodes = module_node.function_nodes
    elif isinstance(node, ClassNode):
        nodes = module_node.class_nodes
    else:
        nodes = module_node.variable_nodes
    text = (source_root / module_node.name).read_text()
    source_names = list(get_scope_symbols(ast.parse(text)))
    following_names = (
        source_names[source_names.index(node.name) + 1 :]
        if node.name in source_names
        else []
    )
    for index, other in enumerate(nodes):
        if other.name in following_names:
            nodes.insert(index, node)
            return
    nodes.append(node)
