import typing as T
from groupy.utils.read_source import read_source
from pathlib import Path


def get_module_sources(
    source_root: Path, module_names: T.List[str]
) -> T.Dict[str, str]:
    return {
        module_name: read_source(source_root / module_name)
        for module_name in module_names
    }
