from pathlib import Path


def get_groupy_path(file_name: str) -> Path:
    # The groupy files live in the .groupy dir in the repository root (the cwd)
    return Path(".groupy") / file_name
