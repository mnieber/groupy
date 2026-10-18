import typing as T

from dataclassy import dataclass


@dataclass
class GlossaryEntry:
    name: str
    description: str
    aliases: T.List[str] = []
    abbreviation: T.Optional[str] = None
