import typing as T
from pathlib import Path

from groupy.groups.models.group import Group


def load_group_file(group_file_path: Path) -> T.List[Group]:
    groups_by_nr: T.Dict[int, Group] = {}
    for line in group_file_path.read_text().splitlines():
        if not line.strip():
            continue
        module_name, group_nr = line.rsplit(" ", 1)
        group = groups_by_nr.setdefault(int(group_nr), Group(nr=int(group_nr)))
        group.module_names.append(module_name)
    return [groups_by_nr[nr] for nr in sorted(groups_by_nr)]
