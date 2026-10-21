import typing as T

from groupy.utils.matches_glob import matches_glob


def get_active_module_names(
    module_names: T.List[str], exclude_patterns: T.List[str]
) -> T.List[str]:
    return [
        module_name
        for module_name in module_names
        if not any(matches_glob(module_name, pattern) for pattern in exclude_patterns)
    ]
