from groupy.sessions.models.session import Session
from groupy.sessions.rules.load_branch_session import load_branch_session
from groupy.sessions.utils.exceptions import NoGroupyBranchError
from groupy.utils.has_git_branch import has_git_branch


def get_groupy_branch_session(branch_name: str) -> Session:
    # Raises a NoGroupyBranchError when the branch doesn't exist or has no session
    if not has_git_branch(branch_name):
        raise NoGroupyBranchError(f"The branch {branch_name} doesn't exist")
    return load_branch_session(f"refs/heads/{branch_name}")
