import typing as T

from groupy.utils.run_git import run_git


def get_uncommitted_changes() -> T.List[str]:
    # The lines of git status, which include the untracked files
    return run_git("status", "--porcelain").splitlines()
