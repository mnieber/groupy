import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

__all__ = ["Context", "TestEnv"]


class TestEnv(GroupyNextTestEnv):
    # Actions

    def write_last_run(self, **fields: T.Any) -> None:
        """Writes the last-run file (which is excluded from git), as groupy
        next would leave it behind."""
        lines = [f"{field}: {value}" for field, value in fields.items()]
        self.write_file(".groupy/last-run.yaml", "\n".join(lines) + "\n")
