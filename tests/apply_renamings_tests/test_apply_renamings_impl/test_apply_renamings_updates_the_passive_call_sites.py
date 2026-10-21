from apply_renamings_tests.apply_renamings_test_env import Context, TestEnv

from groupy.nodes.actions.set_rename_to import set_rename_to

SUMMARY = "myapp/reports/summary.py"

SUMMARY_PY = """\
from myapp.books import create_book


def summarize(title):
    return create_book(title).title
"""

RENAMED_SUMMARY_PY = """\
from myapp.books import make_book


def summarize(title):
    return make_book(title).title
"""


def create_env(context: Context):
    return Env(context)


def test_apply_renamings_updates_the_passive_call_sites(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-renamings. Besides the modules of the base env, myapp has the
    # reports package, which the developer excludes. The summarize function in
    # the reports package calls create_book, which is renamed to make_book.
    if env.step(
        env.create_session_at_apply_renamings(
            {"myapp/reports/__init__.py": "", SUMMARY: SUMMARY_PY}
        ),
        env.set_session_exclude("myapp/reports/**"),
        env.edit_node_file(set_rename_to, "myapp/books.py", "create_book", "make_book"),
        env.commit_all("review the renamings"),
    ):
        pass

    # We run groupy next.
    #
    # The renaming should also update the import and the call site in the
    # passive summary module.
    if env.step(
        env.run_groupy("next"),
    ):
        assert "def make_book(title):" in env.read_module("myapp/books.py")
        assert env.read_module(SUMMARY) == RENAMED_SUMMARY_PY


class Env(TestEnv):
    pass
