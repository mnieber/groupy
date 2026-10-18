import typing as T

from dataclassy import dataclass


@dataclass
class Rfr:
    id: str
    prompt: str
    context: T.Dict[str, T.Any] = {}
