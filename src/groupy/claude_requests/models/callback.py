import typing as T

from dataclassy import dataclass


@dataclass
class Callback:
    name: str
    args: T.Dict[str, T.Any] = {}
