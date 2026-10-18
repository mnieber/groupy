import typing as T

from dataclassy import dataclass


@dataclass
class Rfa:
    id: str
    prompt: str
    context: T.Dict[str, T.Any] = {}
