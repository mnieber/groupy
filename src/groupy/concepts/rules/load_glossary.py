from pathlib import Path

import yaml
from groupy.concepts.models.glossary import Glossary
from groupy.concepts.models.glossary_entry import GlossaryEntry


def load_glossary(glossary_path: Path) -> Glossary:
    # A missing glossary file is an empty glossary
    if not glossary_path.exists():
        return Glossary()
    items = yaml.safe_load(glossary_path.read_text()) or []
    return Glossary(
        entries=[
            GlossaryEntry(
                **{key: value for key, value in item.items() if value is not None}
            )
            for item in items
        ]
    )
