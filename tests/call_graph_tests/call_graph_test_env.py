import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest

from groupy.call_graph.actions.build_call_graph import build_call_graph
from groupy.call_graph.models.call_edge import CallEdge
from groupy.call_graph.models.call_graph import CallGraph
from groupy.call_graph.rules.load_call_graph import load_call_graph

TITLES_PY = """\
def format_title(title):
    return capitalize(title.strip())


def capitalize(text):
    return text.title()
"""

BOOKS_PY = """\
from myapp.titles import format_title


class Book:
    def __init__(self, title):
        self.title = title

    def save(self):
        self._validate()

    def _validate(self):
        assert self.title


def create_book(title):
    return Book(format_title(title))
"""

AUTHORS_PY = """\
import myapp.titles as titles


class Author:
    def __init__(self, name):
        self.name = titles.capitalize(name)

    def save(self):
        pass


def publish(item):
    item.save()
"""


@dataclass
class Context:
    """The pytest fixtures that call graph tests need. repo_dir holds the
    target code (in src) and the .groupy dir."""

    repo_dir: Path
    monkeypatch: pytest.MonkeyPatch


class TestEnv:
    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.source_root = context.repo_dir / "src"
        self.groupy_dir = context.repo_dir / ".groupy"
        self.call_graph: CallGraph = None
        self.error: Exception = None
        self.__post_init__()

    def __post_init__(self):
        """Post-initialization hook for subclasses."""

    def step(self, *_: None) -> bool:
        return True

    # Actions

    def write_module(self, module_name: str, text: str) -> None:
        path = self.source_root / module_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def write_myapp_modules(self) -> None:
        """Writes myapp/titles.py, myapp/books.py and myapp/authors.py."""
        self.write_module("myapp/__init__.py", "")
        self.write_module("myapp/titles.py", TITLES_PY)
        self.write_module("myapp/books.py", BOOKS_PY)
        self.write_module("myapp/authors.py", AUTHORS_PY)

    def delete_module(self, module_name: str) -> None:
        (self.source_root / module_name).unlink()

    def build_call_graph(self, file_name: str = "call-graph.yaml") -> None:
        """Builds the call graph of the target code into .groupy/file_name."""
        build_call_graph(self.source_root, self.groupy_dir / file_name)

    def load_call_graph(
        self, file_name: str = "call-graph.yaml", store_as: str = "call_graph"
    ) -> None:
        setattr(self, store_as, load_call_graph(self.groupy_dir / file_name))

    # Queries (for use in asserts)

    def callees_of(self, caller: str) -> T.Set[T.Tuple[str, bool]]:
        """Returns the (callee, is_certain) pairs of the edges of caller."""
        return {
            (edge.callee, edge.is_certain)
            for edge in self.call_graph.edges
            if edge.caller == caller
        }

    def edge(self, caller: str, callee: str) -> CallEdge:
        matches = [
            edge
            for edge in self.call_graph.edges
            if edge.caller == caller and edge.callee == callee
        ]
        assert len(matches) == 1, f"Expected one edge from {caller} to {callee}"
        return matches[0]

    def edge_set(
        self, call_graph: CallGraph
    ) -> T.Set[T.Tuple[str, str, str, int, bool]]:
        return {
            (edge.caller, edge.callee, edge.file, edge.line, edge.is_certain)
            for edge in call_graph.edges
        }

    def line_of(self, module_name: str, snippet: str) -> int:
        """Returns the (1-based) number of the line of the module that contains
        the snippet."""
        lines = (self.source_root / module_name).read_text().splitlines()
        matches = [nr for nr, line in enumerate(lines, start=1) if snippet in line]
        assert len(matches) == 1, f"Expected one line with {snippet}"
        return matches[0]
