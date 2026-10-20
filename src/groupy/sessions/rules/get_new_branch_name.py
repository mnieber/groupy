import re

from groupy.sessions.rules.get_groupy_path import get_groupy_path


def get_new_branch_name() -> str:
    # The per-branch dirs outlive their branches, so that a branch name is never
    # reused
    groupy_dir = get_groupy_path("")
    numbers = [
        int(match.group(1))
        for path in (groupy_dir.iterdir() if groupy_dir.is_dir() else [])
        if path.is_dir()
        for match in [re.fullmatch(r"groupy-(\d+)", path.name)]
        if match
    ]
    return f"groupy-{max(numbers, default=0) + 1}"
