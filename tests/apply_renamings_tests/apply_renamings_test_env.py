import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

__all__ = ["Context", "TestEnv"]

STAGE = "apply-renamings"


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the apply-renamings stage. The target code (in the src
    dir) has the modules of the base env plus the modules that the test adds.
    With the simple grouping strategy and large sizes, all modules are in the
    chunk group-1/chunk-1."""

    # Actions

    def create_session_at_apply_renamings(self, modules: T.Dict[str, str]) -> None:
        """Creates a session for the target code with the added modules, whose
        next stage is apply-renamings."""
        self.create_session(
            modules,
            grouping_strategy="simple",
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.set_next_stage(STAGE)
