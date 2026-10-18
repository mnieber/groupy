import typing as T

from groupy.utils.run_git import run_git


def get_changed_files() -> T.List[str]:
    # The paths (relative to the repository root) of the files that differ from the
    # last commit, including untracked files
    paths = []
    for line in run_git("status", "--porcelain", "--untracked-files=all").splitlines():
        path = line[3:]
        # A renamed file is listed as <old path> -> <new path>
        paths.append(path.split(" -> ")[-1].strip('"'))
    return paths
