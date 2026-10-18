from dataclassy import dataclass


@dataclass
class CallEdge:
    caller: str
    callee: str
    file: str
    line: int
    is_certain: bool
