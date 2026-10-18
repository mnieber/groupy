import typing as T
from pathlib import Path

from groupy.groups.actions.save_group_file import save_group_file
from groupy.groups.models.group import Group
from groupy.groups.rules.load_group_file import load_group_file


def add_file_to_group(
    group_file_path: Path,
    module_name: str,
    group_module_name: T.Optional[str] = None,
) -> None:
    # A new module goes into the group of group_module_name (e.g. the module that
    # its code came from) if given, or else into the group of a module in the same
    # dir, or else into a new group
    groups = load_group_file(group_file_path)
    if any(module_name in group.module_names for group in groups):
        return
    module_dir = Path(module_name).parent
    for group in groups:
        if group_module_name is not None:
            is_match = group_module_name in group.module_names
        else:
            is_match = any(
                Path(each).parent == module_dir for each in group.module_names
            )
        if is_match:
            group.module_names = sorted([*group.module_names, module_name])
            break
    else:
        next_nr = max([group.nr for group in groups], default=0) + 1
        groups.append(Group(nr=next_nr, module_names=[module_name]))
    save_group_file(groups, group_file_path)
