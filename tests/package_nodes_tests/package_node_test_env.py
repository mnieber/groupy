from dataclasses import dataclass
from pathlib import Path

import pytest

from groupy.package_nodes.actions.create_package_node_file import (
    create_package_node_file,
)
from groupy.package_nodes.models.package_node import PackageNode
from groupy.package_nodes.rules.load_package_node import load_package_node


@dataclass
class Context:
    """The pytest fixtures that package node tests need. source_root is the
    (not yet existing) directory that holds the target code."""

    source_root: Path
    monkeypatch: pytest.MonkeyPatch


class TestEnv:
    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.source_root = context.source_root
        self.package_node: PackageNode = None
        self.__post_init__()

    def __post_init__(self):
        """Post-initialization hook for subclasses."""

    def step(self, *_: None) -> bool:
        return True

    # Actions

    def write_file(self, relative_path: str, text: str = "") -> None:
        """Writes a file, where relative_path is relative to the source root
        (e.g. `myapp/books.py`)."""
        path = self.source_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def create_package_node_file(self, package_name: str) -> None:
        create_package_node_file(self.source_root, package_name)

    def load_package_node(
        self, package_name: str, store_as: str = "package_node"
    ) -> None:
        """Loads the node file of the package into the env attribute
        store_as."""
        node_file_path = self.source_root / package_name / "package-node.groupy.yaml"
        setattr(self, store_as, load_package_node(node_file_path))

    # Queries (for use in asserts)

    def file_exists(self, relative_path: str) -> bool:
        return (self.source_root / relative_path).exists()
