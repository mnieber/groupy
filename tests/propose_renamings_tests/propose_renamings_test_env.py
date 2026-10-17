import typing as T

from groupy.claude_requests.models.callback import Callback
from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

__all__ = ["Context", "TestEnv"]

STAGE = "propose-renamings"

RFA_ID = "propose-renamings/group-1/chunk-1"

RETRY_RFA_ID = "propose-renamings/group-1/chunk-1/retry-1"


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the propose-renamings stage. The target code (in the src
    dir) has the modules of the base env plus the modules that the test adds.
    With the simple grouping strategy and large sizes, all modules are in the
    chunk group-1/chunk-1."""

    # Actions

    def create_session_at_propose_renamings(
        self, modules: T.Dict[str, str], glossary_text: str = None
    ) -> None:
        """Creates a session (that uses the fake RFA policy) for the target
        code with the added modules, whose next stage is propose-renamings.
        If glossary_text is given, the target code has this glossary file."""
        self.create_session(
            modules,
            grouping_strategy="simple",
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        if glossary_text is not None:
            self.write_file("src/glossary.groupy.yaml", glossary_text)
        self.set_next_stage(STAGE)


def commit_messages(callbacks: T.List[Callback]) -> T.List[str]:
    """Returns the messages of the commits that Groupy makes after running
    the callbacks."""
    return [f"{STAGE}: {callback.name}" for callback in callbacks]
