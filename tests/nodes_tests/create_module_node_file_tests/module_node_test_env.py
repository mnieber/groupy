import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest

from groupy.nodes.actions.create_module_node_file import create_module_node_file
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.rules.load_module_node import load_module_node


@dataclass
class Context:
    """The pytest fixtures that module node tests need. source_root is the
    (not yet existing) directory that holds the target code."""

    source_root: Path
    monkeypatch: pytest.MonkeyPatch


class TestEnv:
    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.source_root = context.source_root
        self.module_node: ModuleNode = None
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

    def load_module_node(self, module_name: str, store_as: str = "module_node") -> None:
        """Loads the node file of the module into the env attribute store_as."""
        node_file_path = self.source_root / f"{module_name}.groupy.yaml"
        setattr(self, store_as, load_module_node(node_file_path))

    # Queries (for use in asserts)

    def file_exists(self, relative_path: str) -> bool:
        return (self.source_root / relative_path).exists()

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
