from pathlib import Path

from groupy.groups.actions.save_group_file import save_group_file
from groupy.groups.rules.load_group_file import load_group_file


def rename_file_in_group_file(
    group_file_path: Path, module_name: str, new_module_name: str
) -> None:
    # A renamed module keeps its group
    groups = load_group_file(group_file_path)
    for group in groups:
        group.module_names = sorted(
            new_module_name if each == module_name else each
            for each in group.module_names
        )
    save_group_file(groups, group_file_path)
