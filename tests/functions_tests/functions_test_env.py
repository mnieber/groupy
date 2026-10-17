import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest
from groupy.functions.actions.move_function_to_parent import (
    move_function_to_parent,
)
from groupy.nodes.actions.create_module_node_file import create_module_node_file
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.rules.load_module_node import load_module_node


@dataclass
class Context:
    """The pytest fixtures that function tests need. source_root is the (not
    yet existing) directory that holds the target code."""

    source_root: Path
    monkeypatch: pytest.MonkeyPatch


class TestEnv:
    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.source_root = context.source_root
        self.module_node: ModuleNode = None
        self.remembered_node_file_text: str = None
        self.error: Exception = None
        self.__post_init__()

    def __post_init__(self):
        """Post-initialization hook for subclasses."""

    def step(self, *_: None) -> bool:
        return True

    # Actions

    def write_module(self, module_name: str, text: str) -> None:
        """Writes the module, where module_name is its path relative to the
        source root (e.g. `myapp/books.py`)."""
        path = self.source_root / module_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def create_module_node_file(self, module_name: str) -> None:
        create_module_node_file(self.source_root, module_name)

    def move_function_to_parent(
        self, module_name: str, function_location: str, parent_location: str
    ) -> None:
        move_function_to_parent(
            self.source_root, module_name, function_location, parent_location
        )

    def move_function_to_parent_and_catch_error(
        self, module_name: str, function_location: str, parent_location: str
    ) -> None:
        """Runs move_function_to_parent and stores the exception it is
        expected to raise in env.error."""
        self.error = None
        try:
            self.move_function_to_parent(
                module_name, function_location, parent_location
            )
        except Exception as error:
            self.error = error

    def load_module_node(self, module_name: str) -> None:
        """Loads the node file of the module into env.module_node."""
        self.module_node = load_module_node(
            self.source_root / f"{module_name}.groupy.yaml"
        )

    def remember_node_file(self, module_name: str) -> None:
        self.remembered_node_file_text = self.read_file(f"{module_name}.groupy.yaml")

    # Queries (for use in asserts)

    def read_file(self, relative_path: str) -> str:
        return (self.source_root / relative_path).read_text()

    def names(self, nodes: T.List[T.Any]) -> T.List[str]:
        return [node.name for node in nodes]

    def function_node(self, name: str):
        return _find_node(self.module_node.function_nodes, name)

    def class_node(self, name: str):
        return _find_node(self.module_node.class_nodes, name)


def _find_node(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]
