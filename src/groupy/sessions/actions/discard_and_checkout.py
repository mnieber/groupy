from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.models.session import reset_session
from groupy.utils.run_git import run_git


def discard_and_checkout(branch_name: str) -> None:
    # The uncommitted changes are lost, but not the per-branch dirs, which are
    # excluded from git
    restore_working_tree()
    run_git("checkout", branch_name)
    reset_session()
