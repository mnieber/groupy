import typing as T

from groupy_next_tests.groupy_next_test_env import (
    FAKE_REFACTORING_POLICY,
    FAKE_RFA_POLICY,
    FAKE_RFR_POLICY,
    Context,
)
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

from groupy.nodes.rules.get_active_module_names import get_active_module_names
from groupy.nodes.rules.get_target_module_names import get_target_module_names
from groupy.sessions.models.session import reset_session
from groupy.sessions.rules.get_exclude_patterns import get_exclude_patterns

__all__ = ["Context", "TestEnv"]

SUMMARY_PY = """\
from myapp.books import create_book


def summarize(title):
    return create_book(title).title
"""

LEGACY_PY = """\
def archive_book(book):
    return {"archived": book}
"""


class TestEnv(GroupyNextTestEnv):
    def __init__(self, context: Context):
        self.exclude_patterns: T.List[str] = []
        self.active_module_names: T.List[str] = []
        super().__init__(context)

    # Actions

    def create_repo_with_reports(self) -> None:
        """Creates a git repo with the myapp package in the src dir (see
        create_repo_with_target_code), plus the myapp/reports package, and
        commits it. The tests exclude myapp/reports."""
        self.create_repo_with_target_code()
        self.write_file("src/myapp/reports/__init__.py", "")
        self.write_file("src/myapp/reports/summary.py", SUMMARY_PY)
        self.commit_all("add reports")

    def create_session_with_reports(self, *exclude_patterns: str) -> None:
        """Creates a git repo with the myapp package in the src dir, plus the
        myapp/legacy.py module and the myapp/reports package, and a config file
        that uses the fake policies and the package grouping strategy. Then it
        runs groupy init with the exclude patterns, and the first stage
        (group-modules). The chunks are group-1/chunk-1 (the modules of myapp,
        including legacy.py), group-2/chunk-1 (myapp/chapters) and
        group-3/chunk-1 (myapp/reports)."""
        self.create_repo_with_reports()
        self.write_file("src/myapp/legacy.py", LEGACY_PY)
        config_lines = [
            f"rfa_policy: {FAKE_RFA_POLICY}",
            f"rfr_policy: {FAKE_RFR_POLICY}",
            f"refactoring_policy: {FAKE_REFACTORING_POLICY}",
            "grouping_strategy: package",
            "max_group_lines: 10000",
            "max_chunk_lines: 10000",
        ]
        self.write_file(".groupy/config.yaml", "\n".join(config_lines) + "\n")
        self.commit_all("add legacy and the groupy config")
        self.run_groupy(
            "init",
            "--accept-risks",
            "--target-dir=src",
            *[f"--exclude={pattern}" for pattern in exclude_patterns],
        )
        # The first stage (group-modules) creates the group file
        self.run_groupy("next")

    def load_active_module_names(self) -> None:
        """Loads the exclude patterns of the session (in env.exclude_patterns)
        and the names of the active modules of the target code (in
        env.active_module_names), as a stage does when it starts."""
        # Each stage runs in a new process, which loads the session file anew
        reset_session()
        self.exclude_patterns = get_exclude_patterns()
        self.active_module_names = get_active_module_names(
            get_target_module_names(self.repo_dir / "src"), self.exclude_patterns
        )

    # Queries (for use in asserts)

    def grouped_module_names(self) -> T.Set[str]:
        return {
            module_name for group in self.groups for module_name in group.module_names
        }
