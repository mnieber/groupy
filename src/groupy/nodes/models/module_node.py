import typing as T

from dataclassy import dataclass
from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.variable_node import VariableNode


@dataclass
class ModuleNode:
    name: str
    rename_to: T.Optional[str] = None
    line_count: int = 0
    concepts: T.Dict[str, T.Optional[str]] = {}
    renamings: T.Dict[str, str] = {}
    function_nodes: T.List[FunctionNode] = []
    class_nodes: T.List[ClassNode] = []
    variable_nodes: T.List[VariableNode] = []
