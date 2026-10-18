import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest

from groupy.groups.models.chunk import Chunk
from groupy.groups.models.group import Group
from groupy.groups.rules.create_package_groups import create_package_groups
from groupy.groups.rules.create_simple_groups import create_simple_groups
from groupy.groups.rules.split_group_into_chunks import split_group_into_chunks
from groupy.nodes.actions.create_module_node_file import create_module_node_file
from groupy.package_nodes.actions.create_package_node_file import (
    create_package_node_file,
)


@dataclass
class Context:
    """The pytest fixtures that groups tests need. source_root is the (not yet
    existing) directory that holds the target code."""

    source_root: Path
    monkeypatch: pytest.MonkeyPatch


class TestEnv:
    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.source_root = context.source_root
        self.groups: T.List[Group] = []
        self.chunks: T.List[Chunk] = []
        self.__post_init__()

    def __post_init__(self):
        """Post-initialization hook for subclasses."""

    def step(self, *_: None) -> bool:
        return True

    # Actions

    def write_module(self, module_name: str, line_count: int) -> None:
        """Writes a module with line_count lines, without a node file."""
        path = self.source_root / module_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(f"x{nr} = {nr}\n" for nr in range(line_count)))

    def add_module(self, module_name: str, line_count: int) -> None:
        """Writes a module with line_count lines, and creates its node file."""
        self.write_module(module_name, line_count)
        create_module_node_file(self.source_root, module_name)

    def add_modules(self, line_count_per_module: T.Dict[str, int]) -> None:
        for module_name, line_count in line_count_per_module.items():
            self.add_module(module_name, line_count)

    def create_package_node_file(self, package_name: str) -> None:
        create_package_node_file(self.source_root, package_name)

    def create_simple_groups(self, max_group_lines: int) -> None:
        self.groups = create_simple_groups(self.source_root, max_group_lines)

    def create_package_groups(self) -> None:
        self.groups = create_package_groups(self.source_root)

    def split_group_into_chunks(
        self, module_names: T.List[str], max_chunk_lines: int, group_nr: int = 1
    ) -> None:
        group = Group(nr=group_nr, module_names=module_names)
        self.chunks = split_group_into_chunks(self.source_root, group, max_chunk_lines)

    # Queries (for use in asserts)

    def module_names_per_group(self) -> T.List[T.List[str]]:
        return [group.module_names for group in self.groups]

    def group_nrs(self) -> T.List[int]:
        return [group.nr for group in self.groups]

    def module_names_per_chunk(self) -> T.Dict[str, T.List[str]]:
        return {chunk.id: chunk.module_names for chunk in self.chunks}
