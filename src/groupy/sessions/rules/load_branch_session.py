import yaml

from groupy.sessions.models.session import Session
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.utils.exceptions import NoGroupyBranchError
from groupy.utils.try_run_git import try_run_git


def load_branch_session(revision: str) -> Session:
    # Loads the session file of a branch (or of another revision), without a
    # checkout. A groupy branch is a branch with a session file.
    # The "./" makes git resolve the path from the cwd instead of the repo root
    session_path = get_groupy_path("session.yaml").as_posix()
    text = try_run_git("show", f"{revision}:./{session_path}")
    if text is None:
        raise NoGroupyBranchError(f"{revision} is not a groupy branch")
    return Session(**yaml.safe_load(text))
