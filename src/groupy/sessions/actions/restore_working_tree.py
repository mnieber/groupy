from groupy.utils.run_git import run_git


def restore_working_tree() -> None:
    # Discards all uncommitted changes, also new files (but not ignored files)
    run_git("reset", "--hard", "HEAD")
    run_git("clean", "-fd")
