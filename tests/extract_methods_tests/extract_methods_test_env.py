import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

from groupy.claude_requests.models.callback import Callback

__all__ = ["Context", "TestEnv"]

STAGE = "extract-methods"


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the extract-methods stage. The target code (in the src
    dir) has the modules of the base env plus the modules that the test
    adds."""

    # Actions

    def create_session_at_extract_methods(
        self, modules: T.Dict[str, str], grouping_strategy: str = "simple"
    ) -> None:
        """Creates a session for the target code with the added modules, whose
        next stage is extract-methods. With the simple grouping strategy, all
        modules are in the chunk group-1/chunk-1. With the package grouping
        strategy, the modules of myapp/chapters are in the chunk
        group-2/chunk-1."""
        self.create_session(
            modules,
            grouping_strategy=grouping_strategy,
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.set_next_stage(STAGE)


def commit_messages(callbacks: T.List[Callback]) -> T.List[str]:
    """Returns the messages of the commits that Groupy makes after running
    the callbacks."""
    return [f"{STAGE}: {callback.name}" for callback in callbacks]
