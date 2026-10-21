from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.sessions.utils.exceptions import BranchDirsNotIgnoredError
from groupy.utils.try_run_git import try_run_git


def check_branch_dirs_are_ignored(branch_name: str) -> None:
    # The per-branch dirs are not committed, so the .gitignore in the dir from
    # which Groupy runs must ignore them (it has to be committed on the base
    # branch, so that the dirs don't make the working tree unclean there)
    probe_path = (get_branch_dir(branch_name) / "last-run.yaml").as_posix()
    if try_run_git("check-ignore", "-q", probe_path) is None:
        raise BranchDirsNotIgnoredError(
            "The per-branch dirs of Groupy must be ignored by git: commit a "
            ".gitignore with the line /.groupy/*/ in the dir from which you "
            "run Groupy"
        )
