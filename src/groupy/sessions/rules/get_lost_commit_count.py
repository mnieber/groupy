from groupy.utils.get_git_branches import get_git_branches
from groupy.utils.run_git import run_git


def get_lost_commit_count(branch_name: str) -> int:
    # Counts the commits of the branch that are on no other branch
    other_branches = [
        f"refs/heads/{name}" for name in get_git_branches() if name != branch_name
    ]
    return int(
        run_git(
            "rev-list", "--count", f"refs/heads/{branch_name}", "--not", *other_branches
        )
    )
