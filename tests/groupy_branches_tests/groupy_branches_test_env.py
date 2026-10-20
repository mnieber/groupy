import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv
from groupy_next_tests.groupy_next_test_env import callback

__all__ = ["Context", "TestEnv"]

RFA_ID_1 = "identify-helper-functions/group-1/chunk-1"

RFA_ID_2 = "identify-helper-functions/group-2/chunk-1"


class TestEnv(GroupyNextTestEnv):
    # Actions

    def create_session_with_two_chunks(self) -> None:
        """Creates a session (on branch groupy-1) for the myapp package, with
        the package grouping strategy, so that the modules of myapp (group 1)
        and of myapp/chapters (group 2) are in different chunks. The first
        stage is replaced by a fake stage that makes an RFA per chunk, and the
        RFAs of both chunks have a script."""
        self.create_session(
            grouping_strategy="package", max_group_lines=10000, max_chunk_lines=10000
        )
        self.install_fake_stage()
        self.script_rfa(
            RFA_ID_1,
            callback(
                "add_responsibility",
                module_name="myapp/books.py",
                location="create_book",
                responsibility="Creates a book",
            ),
        )
        self.script_rfa(
            RFA_ID_2,
            callback(
                "add_responsibility",
                module_name="myapp/chapters/create_chapter.py",
                location="create_chapter",
                responsibility="Creates a chapter",
            ),
        )

    # Queries (for use in asserts)

    def branch_tags(self, branch_name: str) -> T.Set[str]:
        """Returns the groupy tags of the branch, without the prefix
        groupy/<branch_name>/ (e.g. init, group-modules/start)."""
        prefix = f"groupy/{branch_name}/"
        return {tag[len(prefix) :] for tag in self.git_tags() if tag.startswith(prefix)}
