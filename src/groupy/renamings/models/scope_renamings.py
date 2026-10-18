import typing as T

from dataclassy import dataclass


@dataclass
class ScopeRenamings:
    # The scope location is @module, a class name or a function location
    scope_location: str
    renamings: T.List[T.Tuple[str, str]] = []
