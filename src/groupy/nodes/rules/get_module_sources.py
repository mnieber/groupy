import typing as T
from pathlib import Path


def get_module_sources(
    source_root: Path, module_names: T.List[str]
) -> T.Dict[str, str]:
    return {
        module_name: (source_root / module_name).read_text()
        for module_name in module_names
    }
