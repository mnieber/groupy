from groupy.utils.try_run_git import try_run_git


def has_git_branch(branch_name: str) -> bool:
    return (
        try_run_git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch_name}")
        is not None
    )
