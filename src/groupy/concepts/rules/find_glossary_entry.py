import typing as T

from groupy.concepts.models.glossary import Glossary
from groupy.concepts.models.glossary_entry import GlossaryEntry
from groupy.concepts.utils.exceptions import AmbiguousEntryError
from groupy.nodes.utils.exceptions import EntryNotFoundError


def find_glossary_entry(
    glossary: Glossary, name: str, meaning_nr: T.Optional[int] = None
) -> GlossaryEntry:
    # The meaning_nr is the (1-based) position of the entry among the entries with
    # the same name
    matches = [entry for entry in glossary.entries if entry.name == name]
    if not matches:
        raise EntryNotFoundError(f"The glossary has no entry {name}")
    if meaning_nr is None:
        if len(matches) > 1:
            raise AmbiguousEntryError(
                f"The glossary has {len(matches)} entries {name}: pass a meaning_nr"
            )
        return matches[0]
    if not 1 <= meaning_nr <= len(matches):
        raise EntryNotFoundError(f"The glossary has no meaning {meaning_nr} of {name}")
    return matches[meaning_nr - 1]
