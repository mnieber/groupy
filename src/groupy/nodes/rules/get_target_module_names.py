import typing as T
from pathlib import Path

from groupy.nodes.rules.is_test_module import is_test_module


def get_target_module_names(source_root: Path) -> T.List[str]:
    # The modules of the target code, without the test code
    module_names = (
        path.relative_to(source_root).as_posix() for path in source_root.rglob("*.py")
    )
    return sorted(
        module_name for module_name in module_names if not is_test_module(module_name)
    )
