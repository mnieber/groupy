import typing as T

from dataclassy import dataclass


@dataclass
class PackageNode:
    name: str
    module_names: T.List[str] = []
    proposed_modules: T.Dict[str, str] = {}
