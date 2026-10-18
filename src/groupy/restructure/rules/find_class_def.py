import ast
import typing as T
from pathlib import Path

from groupy.nodes.rules.get_target_module_names import get_target_module_names


def find_class_def(
    source_root: Path, module_name: str, class_name: str
) -> T.Optional[T.Tuple[str, ast.ClassDef]]:
    # Finds the class that the name refers to in the module (defined in the module,
    # or imported from another module of the target code). Returns the module of
    # the class and its definition.
    tree = ast.parse((source_root / module_name).read_text())
    for statement in tree.body:
        if isinstance(statement, ast.ClassDef) and statement.name == class_name:
            return module_name, statement
    for statement in tree.body:
        if isinstance(statement, ast.ImportFrom) and statement.module:
            for alias in statement.names:
                if (alias.asname or alias.name) == class_name:
                    other_module_name = _find_module_name(source_root, statement.module)
                    if other_module_name:
                        return find_class_def(
                            source_root, other_module_name, alias.name
                        )
    return None


def _find_module_name(source_root: Path, dotted_name: str) -> T.Optional[str]:
    path = dotted_name.replace(".", "/")
    for module_name in (f"{path}.py", f"{path}/__init__.py"):
        if module_name in get_target_module_names(source_root):
            return module_name
    return None
