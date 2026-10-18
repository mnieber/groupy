import typing as T

from dataclassy import dataclass


@dataclass
class LocatedNode:
    location: str
    node: T.Any
    # The list that holds the node (None for the module node)
    siblings: T.Optional[T.List[T.Any]] = None
    parent: T.Optional[T.Any] = None
