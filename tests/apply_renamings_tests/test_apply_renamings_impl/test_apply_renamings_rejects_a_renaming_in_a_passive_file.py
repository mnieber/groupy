from apply_renamings_tests.apply_renamings_test_env import Context, TestEnv

from groupy.nodes.actions.set_rename_to import set_rename_to
from groupy.renamings.actions.propose_renamings import ProposedRenamingHasConflictError
from groupy.renamings.actions.set_renaming import set_renaming

SUMMARY = "myapp/reports/summary.py"

SUMMARY_PY = """\
def summarize(title):
    return title
"""


def create_env(context: Context):
    return Env(context)


def test_apply_renamings_rejects_a_renaming_in_a_passive_file(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-renamings. Besides the modules of the base env, myapp has the
    # reports package, which the developer excludes. During the review, the
    # developer has added a renaming to the passive summary module. The node
    # file of books.py has a renaming without a conflict.
    if env.step(
        env.create_session_at_apply_renamings(
            {"myapp/reports/__init__.py": "", SUMMARY: SUMMARY_PY}
        ),
        env.set_session_exclude("myapp/reports/**"),
        env.edit_node_file(
            set_renaming, "myapp/books.py", "create_book", "title", "book_title"
        ),
        env.edit_node_file(set_rename_to, SUMMARY, "summarize", "summarize_report"),
        env.commit_all("review the renamings"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should raise an error that lists the renaming in the passive file
    # as a conflict, before it applies any renaming.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, ProposedRenamingHasConflictError)
        assert f"{SUMMARY}:summarize: is in a passive file" in str(env.error)
        assert env.commit_messages_since_remembered_head() == []
        assert env.git_status() == ""
        assert "def create_book(title):" in env.read_module("myapp/books.py")
        assert env.read_module(SUMMARY) == SUMMARY_PY
        assert env.session.next_stage == "apply-renamings"


class Env(TestEnv):
    pass
