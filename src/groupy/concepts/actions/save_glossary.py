from pathlib import Path

from groupy.concepts.models.glossary import Glossary
from groupy.utils.dataclass_to_dict import dataclass_to_dict
from groupy.utils.dump_yaml import FlowList, dump_yaml


def save_glossary(glossary: Glossary, glossary_path: Path) -> None:
    # The entries are sorted by name (the sort is stable, so the meanings of a name
    # keep their order), and the aliases are written on one line
    items = []
    for entry in sorted(glossary.entries, key=lambda entry: entry.name):
        item = dataclass_to_dict(entry)
        if "aliases" in item:
            item["aliases"] = FlowList(item["aliases"])
        items.append(item)

    glossary_path.parent.mkdir(parents=True, exist_ok=True)
    glossary_path.write_text(dump_yaml(items))
