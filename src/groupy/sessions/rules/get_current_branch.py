from groupy.sessions.utils.exceptions import DetachedHeadError
from groupy.utils.run_git import run_git


def get_current_branch() -> str:
    # On a detached HEAD, git gives HEAD as the name of the branch
    branch_name = run_git("rev-parse", "--abbrev-ref", "HEAD")
    if branch_name == "HEAD":
        raise DetachedHeadError("The HEAD is detached: there is no current branch")
    return branch_name
