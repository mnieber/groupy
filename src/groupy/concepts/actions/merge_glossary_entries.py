import typing as T
from pathlib import Path

from groupy.concepts.actions.edit_glossary import edit_glossary
from groupy.concepts.rules.find_glossary_entry import find_glossary_entry


def merge_glossary_entries(
    glossary_path: Path,
    name: str,
    into_name: str,
    meaning_nr: T.Optional[int] = None,
    into_meaning_nr: T.Optional[int] = None,
) -> None:
    def _edit(glossary):
        entry = find_glossary_entry(glossary, name, meaning_nr)
        into_entry = find_glossary_entry(glossary, into_name, into_meaning_nr)

        # The merged name and its aliases become aliases of the other entry
        for alias in [entry.name, *entry.aliases]:
            if alias not in into_entry.aliases:
                into_entry.aliases.append(alias)
        if into_entry.abbreviation is None:
            into_entry.abbreviation = entry.abbreviation
        glossary.entries.remove(entry)

    edit_glossary(glossary_path, _edit)
