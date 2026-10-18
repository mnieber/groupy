import typing as T
from pathlib import Path

from groupy.groups.models.group import Group
from groupy.nodes.rules.get_module_names import get_module_names


def create_package_groups(source_root: Path) -> T.List[Group]:
    # The modules are sorted, so the groups are ordered by their first module path
    module_names_by_package_name: T.Dict[str, T.List[str]] = {}
    for module_name in get_module_names(source_root):
        package_name = _get_group_package_name(module_name)
        module_names_by_package_name.setdefault(package_name, []).append(module_name)

    return [
        Group(nr=nr, module_names=module_names)
        for nr, module_names in enumerate(module_names_by_package_name.values(), 1)
    ]


def _get_group_package_name(module_name: str) -> str:
    # A group contains a sub-package of a top-level package (e.g. myapp/books), or
    # the modules that are directly in a top-level package
    parts = module_name.split("/")
    if len(parts) == 1:
        return "."
    if len(parts) == 2:
        return parts[0]
    return "/".join(parts[:2])
