import typing as T
from pathlib import Path

from groupy.sessions.rules.get_current_branch import get_current_branch
from groupy.sessions.rules.get_groupy_path import get_groupy_path


def get_branch_dir(branch_name: T.Optional[str] = None) -> Path:
    # The files that Groupy doesn't commit (e.g. the logs) are kept per branch.
    # Without a branch name, this is the dir of the current branch.
    return get_groupy_path(branch_name or get_current_branch())
