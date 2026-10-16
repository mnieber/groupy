import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest
from breaker.concepts.actions.add_glossary_alias import add_glossary_alias
from breaker.concepts.actions.add_glossary_entry import add_glossary_entry
from breaker.concepts.actions.merge_glossary_entries import merge_glossary_entries
from breaker.concepts.actions.save_glossary import save_glossary
from breaker.concepts.actions.set_glossary_abbreviation import (
    set_glossary_abbreviation,
)
from breaker.concepts.actions.set_glossary_description import (
    set_glossary_description,
)
from breaker.concepts.models.glossary import Glossary, GlossaryEntry
from breaker.concepts.rules.load_glossary import load_glossary


@dataclass
class Context:
    """The pytest fixtures that glossary tests need. source_root is the (not
    yet existing) directory that holds the target code and the glossary."""

    source_root: Path
    monkeypatch: pytest.MonkeyPatch


class TestEnv:
    """A TestEnv with a glossary file (glossary.breaker.yaml in the source
    root). The edits of the env work on this file."""

    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.source_root = context.source_root
        self.glossary_path = context.source_root / "glossary.breaker.yaml"
        self.glossary: Glossary = None
        self.remembered_glossary_text: str = None
        self.error: Exception = None
        self.__post_init__()

    def __post_init__(self):
        """Post-initialization hook for subclasses."""

    def step(self, *_: None) -> bool:
        return True

    # Actions

    def write_glossary(self, text: str) -> None:
        self.glossary_path.parent.mkdir(parents=True, exist_ok=True)
        self.glossary_path.write_text(text)

    def load_glossary(self) -> None:
        self.glossary = load_glossary(self.glossary_path)

    def save_glossary(self, file_name: str = "glossary.breaker.yaml") -> None:
        save_glossary(self.glossary, self.source_root / file_name)

    def add_glossary_entry(self, name: str, description: str) -> None:
        add_glossary_entry(self.glossary_path, name, description)

    def set_glossary_description(
        self, name: str, description: str, meaning_nr: int = None
    ) -> None:
        set_glossary_description(
            self.glossary_path, name, description, meaning_nr=meaning_nr
        )

    def add_glossary_alias(self, name: str, alias: str, meaning_nr: int = None) -> None:
        add_glossary_alias(self.glossary_path, name, alias, meaning_nr=meaning_nr)

    def set_glossary_abbreviation(
        self, name: str, abbreviation: T.Optional[str], meaning_nr: int = None
    ) -> None:
        set_glossary_abbreviation(
            self.glossary_path, name, abbreviation, meaning_nr=meaning_nr
        )

    def merge_glossary_entries(
        self,
        name: str,
        into_name: str,
        meaning_nr: int = None,
        into_meaning_nr: int = None,
    ) -> None:
        merge_glossary_entries(
            self.glossary_path,
            name,
            into_name,
            meaning_nr=meaning_nr,
            into_meaning_nr=into_meaning_nr,
        )

    def catch_error(self, env_action: T.Callable, *args, **kwargs) -> None:
        """Runs the env action and stores the exception it is expected to
        raise in env.error."""
        self.error = None
        try:
            env_action(*args, **kwargs)
        except Exception as error:
            self.error = error

    def remember_glossary_file(self) -> None:
        self.remembered_glossary_text = self.glossary_text()

    # Queries (for use in asserts)

    def read_file(self, file_name: str) -> str:
        return (self.source_root / file_name).read_text()

    def glossary_text(self) -> str:
        return self.glossary_path.read_text()

    def glossary_file_is_unchanged(self) -> bool:
        return self.glossary_text() == self.remembered_glossary_text

    def names(self) -> T.List[str]:
        return [entry.name for entry in self.glossary.entries]

    def entry(self, name: str, meaning_nr: int = 1) -> GlossaryEntry:
        """Returns the entry for the meaning_nr-th meaning of name."""
        matches = [entry for entry in self.glossary.entries if entry.name == name]
        assert len(matches) >= meaning_nr, f"Expected {meaning_nr} entries for {name}"
        return matches[meaning_nr - 1]

    def descriptions(self, name: str) -> T.List[str]:
        return [
            entry.description for entry in self.glossary.entries if entry.name == name
        ]
