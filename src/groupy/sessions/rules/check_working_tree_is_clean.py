from groupy.sessions.utils.exceptions import DirtyWorkingTreeError
from groupy.utils.run_git import run_git


def check_working_tree_is_clean() -> None:
    # Untracked files also make the working tree unclean
    if run_git("status", "--porcelain"):
        raise DirtyWorkingTreeError(
            "The working tree is not clean: commit or remove the changes first"
        )
