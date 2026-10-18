import typing as T
from pathlib import Path

from groupy.nodes.rules.get_target_module_names import get_target_module_names


def get_package_names(source_root: Path) -> T.List[str]:
    # A package is the source root, or a dir below it that contains modules
    # (directly or in a sub-dir), with or without an __init__.py
    package_names = {"."}
    for module_name in get_target_module_names(source_root):
        for parent in Path(module_name).parents:
            package_names.add(str(parent))
    return sorted(package_names)
