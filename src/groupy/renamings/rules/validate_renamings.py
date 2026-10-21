import ast
import typing as T
from pathlib import Path

from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.renamings.rules.find_passive_renamings import find_passive_renamings
from groupy.renamings.rules.find_scope_conflicts import find_scope_conflicts
from groupy.renamings.rules.find_scope_def import find_scope_def
from groupy.renamings.rules.get_scope_renamings import get_scope_renamings
from groupy.renamings.rules.get_scope_symbols import get_scope_symbols


def validate_renamings(
    source_root: Path, module_names: T.List[str], passive_module_names: T.List[str]
) -> T.List[str]:
    # Returns a line <module>:<scope location>: <description> per conflict, sorted.
    # A renaming in a passive file is also a conflict.
    conflicts = []
    for module_name in module_names:
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        tree = ast.parse((source_root / module_name).read_text())
        for scope in get_scope_renamings(module_node):
            scope_def = find_scope_def(tree, scope.scope_location)
            existing_names = set(get_scope_symbols(scope_def)) if scope_def else set()
            for conflict in find_scope_conflicts(scope.renamings, existing_names):
                conflicts.append(f"{module_name}:{scope.scope_location}: {conflict}")
    conflicts.extend(find_passive_renamings(source_root, passive_module_names))
    return sorted(conflicts)
