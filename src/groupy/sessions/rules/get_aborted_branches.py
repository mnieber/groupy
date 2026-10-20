import typing as T

from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.utils.get_git_branches import get_git_branches


def get_aborted_branches() -> T.List[str]:
    # An aborted branch has a per-branch dir, but no branch anymore
    groupy_dir = get_groupy_path("")
    if not groupy_dir.is_dir():
        return []
    branch_names = set(get_git_branches())
    return [
        path.name
        for path in groupy_dir.iterdir()
        if path.is_dir() and path.name not in branch_names
    ]
