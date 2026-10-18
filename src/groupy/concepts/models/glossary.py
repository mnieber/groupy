import typing as T

from dataclassy import dataclass

from groupy.concepts.models.glossary_entry import GlossaryEntry  # noqa


@dataclass
class Glossary:
    entries: T.List[GlossaryEntry] = []
