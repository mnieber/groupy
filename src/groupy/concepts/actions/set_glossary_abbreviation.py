import typing as T
from pathlib import Path

from groupy.concepts.actions.edit_glossary import edit_glossary
from groupy.concepts.rules.find_glossary_entry import find_glossary_entry


def set_glossary_abbreviation(
    glossary_path: Path,
    name: str,
    abbreviation: T.Optional[str],
    meaning_nr: T.Optional[int] = None,
) -> None:
    def _edit(glossary):
        find_glossary_entry(glossary, name, meaning_nr).abbreviation = abbreviation

    edit_glossary(glossary_path, _edit)
