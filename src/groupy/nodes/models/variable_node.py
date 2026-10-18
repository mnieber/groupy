import typing as T

from dataclassy import dataclass


@dataclass
class VariableNode:
    name: str
    rename_to: T.Optional[str] = None
    move_to_file: T.Optional[str] = None
    code_unit_type: T.Optional[str] = None
