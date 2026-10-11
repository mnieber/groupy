import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest
from breaker.nodes.actions.create_module_node_file import create_module_node_file
from breaker.nodes.models.module_node import ModuleNode
from breaker.nodes.rules.find_node import find_node
from breaker.nodes.rules.load_module_node import load_module_node

BOOKS_PY = """\
MAX_CHAPTERS = 10
API_URL = "https://books.example.com"


class Book:
    def __init__(self, title):
        self.title = title

    def add_chapter(self, title):
        return {"book": self, "title": format_title(title)}


def create_book(title):
    title = format_title(title)
    _validate(title)
    return Book(title)


def format_title(title):
    return title.strip().title()


def _validate(title):
    if not title:
        raise ValueError("A book needs a title")
"""


@dataclass
class Context:
    """The pytest fixtures that node edit tests need. source_root is the (not
    yet existing) directory that holds the target code."""

    source_root: Path
    monkeypatch: pytest.MonkeyPatch


class TestEnv:
    """A TestEnv with one module and its node file. The node file edits all
    take (source_root, module_name, location, ...), so they are run with
    edit_node_file(action, location, ...) instead of one env action per edit."""

    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.source_root = context.source_root
        self.module_name: str = None
        self.module_text: str = None
        self.module_node: ModuleNode = None
        self.found_node = None
        self.remembered_node_file_text: str = None
        self.error: Exception = None
        self.__post_init__()

    def __post_init__(self):
        """Post-initialization hook for subclasses."""

    def step(self, *_: None) -> bool:
        return True

    # Actions

    def create_module_with_node_file(
        self, module_name: str = "myapp/books.py", text: str = BOOKS_PY
    ) -> None:
        """Writes the module and creates its node file. The other actions of
        the env work on this module."""
        self.module_name = module_name
        self.module_text = text
        path = self.source_root / module_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        create_module_node_file(self.source_root, module_name)

    def edit_node_file(self, action: T.Callable, location: str, *args) -> None:
        action(self.source_root, self.module_name, location, *args)

    def edit_node_file_and_catch_error(
        self, action: T.Callable, location: str, *args
    ) -> None:
        """Runs the edit and stores the exception it is expected to raise in
        env.error."""
        self.error = None
        try:
            self.edit_node_file(action, location, *args)
        except Exception as error:
            self.error = error

    def load_module_node(self) -> None:
        self.module_node = load_module_node(self._node_file_path())

    def find_node(self, location: str) -> None:
        """Finds the node at the location in env.module_node, and stores it
        in env.found_node."""
        self.found_node = find_node(self.module_node, location)

    def find_node_and_catch_error(self, location: str) -> None:
        self.error = None
        try:
            self.find_node(location)
        except Exception as error:
            self.error = error

    def remember_node_file(self) -> None:
        self.remembered_node_file_text = self._node_file_path().read_text()

    # Queries (for use in asserts)

    def node_file_is_unchanged(self) -> bool:
        return self._node_file_path().read_text() == self.remembered_node_file_text

    def module_is_unchanged(self) -> bool:
        return (self.source_root / self.module_name).read_text() == self.module_text

    def function_node(self, name: str):
        return _find_by_name(self.module_node.function_nodes, name)

    def class_node(self, name: str):
        return _find_by_name(self.module_node.class_nodes, name)

    def method_node(self, class_name: str, name: str):
        return _find_by_name(self.class_node(class_name).method_nodes, name)

    def variable_node(self, name: str):
        return _find_by_name(self.module_node.variable_nodes, name)

    def _node_file_path(self) -> Path:
        return self.source_root / f"{self.module_name}.breaker.yaml"


def _find_by_name(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]
