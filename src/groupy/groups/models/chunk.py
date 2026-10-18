import typing as T

from dataclassy import dataclass


@dataclass
class Chunk:
    group_nr: int
    nr: int
    module_names: T.List[str] = []

    @property
    def id(self) -> str:
        return f"group-{self.group_nr}/chunk-{self.nr}"
