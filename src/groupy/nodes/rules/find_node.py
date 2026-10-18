import typing as T

from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.rules.find_located_node import find_located_node


def find_node(module_node: ModuleNode, location: str) -> T.Any:
    return find_located_node(module_node, location).node
