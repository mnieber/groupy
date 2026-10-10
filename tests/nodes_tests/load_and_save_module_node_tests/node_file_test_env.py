from dataclasses import dataclass
from pathlib import Path

import pytest
from breaker.nodes.actions.save_module_node import save_module_node
from breaker.nodes.models.module_node import ModuleNode
from breaker.nodes.rules.load_module_node import load_module_node


@dataclass
class Context:
    """The pytest fixtures that node file tests need. source_root is the
    (not yet existing) directory that holds the node files."""

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

    def write_file(self, relative_path: str, text: str) -> None:
        path = self.source_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def load_module_node(
        self, relative_path: str, store_as: str = "module_node"
    ) -> None:
        """Loads the node file into the env attribute store_as."""
        setattr(self, store_as, load_module_node(self.source_root / relative_path))

    def save_module_node(self, relative_path: str) -> None:
        """Saves env.module_node to the node file."""
        save_module_node(self.module_node, self.source_root / relative_path)

    # Queries (for use in asserts)

    def read_file(self, relative_path: str) -> str:
        return (self.source_root / relative_path).read_text()
