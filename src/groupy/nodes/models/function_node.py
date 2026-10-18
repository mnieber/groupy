import typing as T

from dataclassy import dataclass


@dataclass
class FunctionNode:
    name: str
    rename_to: T.Optional[str] = None
    move_to_file: T.Optional[str] = None
    code_unit_type: T.Optional[str] = None
    is_helper_candidate: bool = False
    concepts: T.Dict[str, T.Optional[str]] = {}
    local_terms: T.Dict[str, T.Optional[str]] = {}
    responsibilities: T.List[str] = []
    steps: T.List[str] = []
    steps_to_move_to_caller: T.List[str] = []
    extract_method_priority: T.Optional[str] = None
    renamings: T.Dict[str, str] = {}
    aliases: T.Dict[str, T.List[str]] = {}
    abbreviations: T.Dict[str, str] = {}
    helper_function_nodes: T.List["FunctionNode"] = []
