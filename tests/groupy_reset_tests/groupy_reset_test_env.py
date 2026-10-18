from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv
from groupy_next_tests.groupy_next_test_env import callback

__all__ = ["Context", "TestEnv"]

RFA_ID_1 = "identify-helper-functions/group-1/chunk-1"

RFA_ID_2 = "identify-helper-functions/group-2/chunk-1"


class TestEnv(GroupyNextTestEnv):
    def __init__(self, context: Context):
        self.head_before_reset: str = None
        super().__init__(context)

    # Actions

    def create_session_with_two_chunks(self) -> None:
        """Creates a session for the myapp package, with the package grouping
        strategy, so that the modules of myapp (group 1) and of myapp/chapters
        (group 2) are in different chunks. The first stage is replaced by a
        fake stage that makes an RFA per chunk."""
        self.create_session(
            grouping_strategy="package", max_group_lines=10000, max_chunk_lines=10000
        )
        self.install_fake_stage()

    def script_first_chunk(self) -> None:
        self.script_rfa(
            RFA_ID_1,
            callback(
                "add_responsibility",
                module_name="myapp/books.py",
                location="create_book",
                responsibility="Creates a book",
            ),
        )

    def script_second_chunk(self) -> None:
        self.script_rfa(
            RFA_ID_2,
            callback(
                "add_responsibility",
                module_name="myapp/chapters/create_chapter.py",
                location="create_chapter",
                responsibility="Creates a chapter",
            ),
        )

    def remember_head_before_reset(self) -> None:
        self.head_before_reset = self.git_head()

    def run_groupy_reset(self, *args: str, answer: str = None) -> None:
        """Runs groupy reset like the console script does (see run_groupy_cli).
        When groupy asks for confirmation, it gets the answer, and the prompt
        is stored in env.prompts."""
        self.answer_prompts(answer)
        self.run_groupy_cli("reset", *args)
