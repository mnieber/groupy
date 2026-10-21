import typing as T

from groupy.nodes.rules.get_active_module_names import get_active_module_names


def get_passive_module_names(
    module_names: T.List[str], exclude_patterns: T.List[str]
) -> T.List[str]:
    active_module_names = get_active_module_names(module_names, exclude_patterns)
    return [
        module_name
        for module_name in module_names
        if module_name not in active_module_names
    ]
