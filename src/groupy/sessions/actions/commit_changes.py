from groupy.utils.run_git import run_git


def commit_changes(message: str) -> None:
    # Commits all changes in the working tree, if there are any
    run_git("add", "-A")
    if run_git("status", "--porcelain"):
        run_git("commit", "-m", message)
