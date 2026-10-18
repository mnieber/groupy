import typing as T
from pathlib import Path

_SUFFIX = ".groupy.yaml"


def get_module_names(source_root: Path) -> T.List[str]:
    # The modules that have a module node file, sorted by path
    return sorted(
        str(path.relative_to(source_root))[: -len(_SUFFIX)]
        for path in source_root.rglob(f"*.py{_SUFFIX}")
    )
