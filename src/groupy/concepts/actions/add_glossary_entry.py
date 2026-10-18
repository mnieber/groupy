from pathlib import Path

from groupy.concepts.actions.edit_glossary import edit_glossary
from groupy.concepts.models.glossary_entry import GlossaryEntry


def add_glossary_entry(glossary_path: Path, name: str, description: str) -> None:
    # An entry with an existing name adds a meaning of that name
    def _edit(glossary):
        glossary.entries.append(GlossaryEntry(name=name, description=description))

    edit_glossary(glossary_path, _edit)
