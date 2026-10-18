from apply_renamings_tests.apply_renamings_test_env import Context, TestEnv

from groupy.renamings.actions.propose_renamings import ProposedRenamingHasConflictError
from groupy.renamings.actions.set_renaming import set_renaming

HEADINGS = "myapp/headings.py"

HEADINGS_PY = """\
def format_heading(title, text):
    body = text.strip()
    return title + ": " + body
"""


def create_env(context: Context):
    return Env(context)


def test_apply_renamings_rechecks_conflicts(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-renamings. Besides the modules of the base env, myapp has
    # headings.py. During the review, the developer has added the renaming
    # title -> text to format_heading, which clashes with the parameter text.
    # The node file of books.py has a renaming without a conflict.
    if env.step(
        env.create_session_at_apply_renamings({HEADINGS: HEADINGS_PY}),
        env.edit_node_file(
            set_renaming, "myapp/books.py", "create_book", "title", "book_title"
        ),
        env.edit_node_file(set_renaming, HEADINGS, "format_heading", "title", "text"),
        env.commit_all("review the renamings"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should check all renamings before it applies any of them, and
    # raise an error that lists the conflict. No renaming should have been
    # applied, also not the one in books.py (which comes first).
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, ProposedRenamingHasConflictError)
        assert (
            "myapp/headings.py:format_heading: title -> text clashes with the"
            " existing name text" in str(env.error)
        )
        assert env.commit_messages_since_remembered_head() == []
        assert env.git_status() == ""
        assert "def create_book(title):" in env.read_module("myapp/books.py")
        assert env.read_module(HEADINGS) == HEADINGS_PY
        assert env.session.next_stage == "apply-renamings"


class Env(TestEnv):
    pass
