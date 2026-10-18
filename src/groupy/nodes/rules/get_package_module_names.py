import typing as T
from pathlib import Path


def get_package_module_names(source_root: Path, package_name: str) -> T.List[str]:
    # The modules that are directly in the package dir, by their path relative to
    # the source root
    package_dir = source_root / package_name
    return sorted(
        str(path.relative_to(source_root))
        for path in package_dir.iterdir()
        if path.is_file() and path.suffix == ".py"
    )
