import typing as T

from dataclassy import dataclass


@dataclass
class Group:
    nr: int
    module_names: T.List[str] = []
