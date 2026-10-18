from pathlib import Path

from groupy.groups.actions.save_group_file import save_group_file
from groupy.groups.rules.load_group_file import load_group_file


def remove_file_from_group(group_file_path: Path, module_name: str) -> None:
    groups = load_group_file(group_file_path)
    for group in groups:
        if module_name in group.module_names:
            group.module_names.remove(module_name)
    save_group_file([group for group in groups if group.module_names], group_file_path)
