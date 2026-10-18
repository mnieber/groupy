import typing as T
from pathlib import Path

from groupy.concepts.actions.save_glossary import save_glossary
from groupy.concepts.models.glossary import Glossary
from groupy.concepts.rules.load_glossary import load_glossary


def edit_glossary(glossary_path: Path, edit: T.Callable[[Glossary], None]) -> None:
    # The edit raises an error before the glossary is saved if it cannot be done
    glossary = load_glossary(glossary_path)
    edit(glossary)
    save_glossary(glossary, glossary_path)
