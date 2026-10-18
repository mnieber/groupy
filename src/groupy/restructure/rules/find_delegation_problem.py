import ast
import typing as T
from pathlib import Path

from groupy.restructure.rules.find_class_def import find_class_def


def find_delegation_problem(
    source_root: Path, module_name: str, class_name: str, method_name: str
) -> T.Optional[str]:
    # Returns why the method cannot delegate to a new function, or None
    found = find_class_def(source_root, module_name, class_name)
    if found is None:
        return None
    _, class_def = found
    method_def = next(
        (
            statement
            for statement in class_def.body
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
            and statement.name == method_name
        ),
        None,
    )
    if method_def is None:
        return None

    if method_name.startswith("__") and method_name.endswith("__"):
        return "a dunder method cannot delegate"
    decorator_names = {_get_decorator_name(each) for each in method_def.decorator_list}
    for decorator_name in ("property", "classmethod", "staticmethod"):
        if decorator_name in decorator_names:
            return f"a {decorator_name} cannot delegate"
    overridden_class_name = _find_overridden_class(
        source_root, module_name, class_def, method_name
    )
    if overridden_class_name:
        return f"an override of {overridden_class_name}.{method_name} cannot delegate"
    for node in ast.walk(method_def):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "super"
        ):
            return "a method that uses super() cannot delegate"
        if (
            isinstance(node, ast.Attribute)
            and node.attr.startswith("__")
            and not node.attr.endswith("__")
        ):
            return "a method that uses name-mangled attributes cannot delegate"
    return None


def _get_decorator_name(decorator: ast.expr) -> str:
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Name):
        return decorator.id
    return ""


def _find_overridden_class(
    source_root: Path, module_name: str, class_def: ast.ClassDef, method_name: str
) -> T.Optional[str]:
    # Only the base classes in the target code are known
    for base in class_def.bases:
        if not isinstance(base, ast.Name):
            continue
        found = find_class_def(source_root, module_name, base.id)
        if found is None:
            continue
        base_module_name, base_class_def = found
        method_names = [
            statement.name
            for statement in base_class_def.body
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if method_name in method_names:
            return base_class_def.name
        overridden = _find_overridden_class(
            source_root, base_module_name, base_class_def, method_name
        )
        if overridden:
            return overridden
    return None
