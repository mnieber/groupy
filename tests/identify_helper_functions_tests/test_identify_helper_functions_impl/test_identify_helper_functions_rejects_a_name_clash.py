from groupy_next_tests.groupy_next_test_env import callback
from identify_helper_functions_tests.identify_helper_functions_test_env import (
    RFA_ID,
    Context,
    TestEnv,
)

from groupy.renamings.policies.refactoring_policy import RenameConflictError

TITLES_PY = """\
def create_title(text):
    return format_title(text)


def format_title(text):
    return text.title()


def _format_title(text):
    return text.upper()
"""


def create_env(context: Context):
    return Env(context)


def test_identify_helper_functions_rejects_a_name_clash(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, with the module titles.py,
    # which has the functions format_title and _format_title. The RFA of the
    # chunk nests format_title under create_title.
    if env.step(
        env.create_session_with_modules({"myapp/titles.py": TITLES_PY}),
        env.script_rfa(
            RFA_ID,
            callback(
                "move_function_to_parent",
                module_name="myapp/titles.py",
                function_location="format_title",
                parent_location="create_title",
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Renaming format_title to _format_title would clash with the existing
    # _format_title, so Groupy should raise an error, which interrupts the
    # stage. The rename should not have changed any file, and the chunk should
    # not be finished.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, RenameConflictError)
        assert "_format_title" in str(env.error)
        assert env.commit_messages_since_remembered_head() == [
            "identify-helper-functions: mark_helper_candidates",
            "identify-helper-functions: move_function_to_parent",
        ]
        assert env.git_status() == ""
        assert env.read_module("myapp/titles.py") == TITLES_PY
        assert env.session.next_stage == "identify-helper-functions"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
