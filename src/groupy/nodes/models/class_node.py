import typing as T

from dataclassy import dataclass
from groupy.nodes.models.function_node import FunctionNode


@dataclass
class ClassNode:
    name: str
    rename_to: T.Optional[str] = None
    move_to_file: T.Optional[str] = None
    code_unit_type: T.Optional[str] = None
    concepts: T.Dict[str, T.Optional[str]] = {}
    responsibilities: T.List[str] = []
    extract_method_priority: T.Optional[str] = None
    renamings: T.Dict[str, str] = {}
    method_nodes: T.List[FunctionNode] = []
