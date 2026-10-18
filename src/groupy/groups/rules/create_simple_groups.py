import typing as T
from pathlib import Path

from groupy.groups.models.group import Group
from groupy.nodes.rules.get_line_count_by_module_name import (
    get_line_count_by_module_name,
)
from groupy.nodes.rules.get_module_names import get_module_names


def create_simple_groups(source_root: Path, max_group_lines: int) -> T.List[Group]:
    module_names = get_module_names(source_root)
    line_count_by_module_name = get_line_count_by_module_name(source_root, module_names)

    # A group gets modules until the next module would make it too large
    groups: T.List[Group] = []
    group_lines = 0
    for module_name in module_names:
        line_count = line_count_by_module_name[module_name]
        if not groups or group_lines + line_count > max_group_lines:
            groups.append(Group(nr=len(groups) + 1))
            group_lines = 0
        groups[-1].module_names.append(module_name)
        group_lines += line_count
    return groups
