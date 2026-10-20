import typing as T

from groupy.sessions.rules.get_groupy_branch_session import (
    get_groupy_branch_session,
)
from groupy.sessions.utils.exceptions import NoGroupyBranchError
from groupy.utils.get_git_branches import get_git_branches


def get_groupy_branches() -> T.List[str]:
    # The branches that have a session file
    branch_names = []
    for branch_name in get_git_branches():
        try:
            get_groupy_branch_session(branch_name)
        except NoGroupyBranchError:
            continue
        branch_names.append(branch_name)
    return branch_names
