import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

__all__ = ["Context", "TestEnv"]

STAGE = "apply-move-steps-to-caller"


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the apply-move-steps-to-caller stage. The target code (in the src
    dir) has the modules of the base env plus the modules that the test
    adds."""

    # Actions

    def create_session_at_apply_move_steps_to_caller(
        self, modules: T.Dict[str, str], grouping_strategy: str = "package"
    ) -> None:
        """Creates a session for the target code with the added modules, whose
        next stage is apply-move-steps-to-caller. With the package grouping
        strategy, the modules of myapp are in the chunk group-1/chunk-1, and
        the modules of myapp/chapters are in the chunk group-2/chunk-1."""
        self.create_session(
            modules,
            grouping_strategy=grouping_strategy,
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.set_next_stage(STAGE)
