import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest
from sessions_tests.groupy_test_env import TestEnv as GroupyTestEnv

from groupy.functions.actions.add_responsibility import add_responsibility
from groupy.functions.actions.move_function_to_parent import move_function_to_parent
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.models.package_node import PackageNode
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.nodes.rules.load_package_node import load_package_node

__all__ = ["Context", "TestEnv"]


@dataclass
class Context:
    """The pytest fixtures that groupy sync tests need. repo_dir is the (not
    yet existing) directory of the git repo that holds the target code, and
    capsys captures the report of groupy sync."""

    repo_dir: Path
    monkeypatch: pytest.MonkeyPatch
    capsys: pytest.CaptureFixture


class TestEnv(GroupyTestEnv):
    def __init__(self, context: Context):
        self.source_root = context.repo_dir / "src"
        self.output_lines: T.List[str] = []
        self.module_node: ModuleNode = None
        self.package_node: PackageNode = None
        super().__init__(context)

    # Actions

    def create_session(self) -> None:
        """Creates a git repo with the target code in the src dir, and runs
        groupy init."""
        self.create_repo_with_target_code()
        self.run_groupy("init", "--target-dir=src")

    def run_groupy_sync(self) -> None:
        """Runs groupy sync and stores the lines that it prints in
        env.output_lines."""
        self.context.capsys.readouterr()
        self.run_groupy("sync")
        self.output_lines = self.context.capsys.readouterr().out.splitlines()

    def add_responsibility(
        self, module_name: str, location: str, responsibility: str
    ) -> None:
        add_responsibility(self.source_root, module_name, location, responsibility)

    def move_function_to_parent(
        self, module_name: str, function_location: str, parent_location: str
    ) -> None:
        move_function_to_parent(
            self.source_root, module_name, function_location, parent_location
        )

    def delete_file(self, relative_path: str) -> None:
        (self.repo_dir / relative_path).unlink()

    def load_module_node(self, module_name: str) -> None:
        self.module_node = load_module_node(
            self.source_root / f"{module_name}.groupy.yaml"
        )

    def load_package_node(self, package_name: str) -> None:
        self.package_node = load_package_node(
            self.source_root / package_name / "package-node.groupy.yaml"
        )

    # Queries (for use in asserts)

    def names(self, nodes: T.List[T.Any]) -> T.List[str]:
        return [node.name for node in nodes]

    def function_node(self, name: str):
        return _find_by_name(self.module_node.function_nodes, name)

    def class_node(self, name: str):
        return _find_by_name(self.module_node.class_nodes, name)

    def changed_files(self) -> T.Set[str]:
        """Returns the paths of the files that differ from the last commit,
        including untracked files."""
        changed = self._git("diff", "--name-only", "HEAD").splitlines()
        untracked = self._git("ls-files", "--others", "--exclude-standard")
        return set(changed + untracked.splitlines())


def _find_by_name(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]
