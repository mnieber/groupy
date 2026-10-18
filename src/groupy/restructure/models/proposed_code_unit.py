import typing as T

from dataclassy import dataclass


@dataclass
class ProposedCodeUnit:
    module_name: str
    # The location in the node file, and in the source
    location: str
    source_location: str
    node: T.Any
    # One of top-level, method or helper
    kind: str
    # The code unit type of a helper function is the type of its parent, and the
    # type of a method is the type of its class, unless the method delegates
    code_unit_type: T.Optional[str] = None
    target_file: T.Optional[str] = None
    is_delegating: bool = False
