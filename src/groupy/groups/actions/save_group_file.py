import typing as T
from pathlib import Path

from groupy.groups.models.group import Group


def save_group_file(groups: T.List[Group], group_file_path: Path) -> None:
    # Every line contains a module path and its group number
    lines = [
        f"{module_name} {group.nr}\n"
        for group in groups
        for module_name in group.module_names
    ]
    group_file_path.parent.mkdir(parents=True, exist_ok=True)
    group_file_path.write_text("".join(lines))
