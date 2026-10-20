import typing as T

from groupy.utils.run_git import run_git


def get_git_branches() -> T.List[str]:
    # The local branches
    return run_git("for-each-ref", "--format=%(refname:short)", "refs/heads").split()
