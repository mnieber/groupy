import typing as T
from pathlib import Path

from groupy.concepts.actions.edit_glossary import edit_glossary
from groupy.concepts.rules.find_glossary_entry import find_glossary_entry


def add_glossary_alias(
    glossary_path: Path, name: str, alias: str, meaning_nr: T.Optional[int] = None
) -> None:
    def _edit(glossary):
        entry = find_glossary_entry(glossary, name, meaning_nr)
        if alias not in entry.aliases:
            entry.aliases.append(alias)

    edit_glossary(glossary_path, _edit)
