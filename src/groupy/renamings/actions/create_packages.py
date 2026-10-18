from pathlib import Path, PurePosixPath


def create_packages(source_root: Path, module_name: str) -> None:
    # A package dir of the module that does not exist yet is created with an empty
    # __init__.py
    for package_dir in reversed(PurePosixPath(module_name).parents):
        if str(package_dir) == ".":
            continue
        path = source_root / package_dir
        if not path.exists():
            path.mkdir()
            (path / "__init__.py").write_text("")
