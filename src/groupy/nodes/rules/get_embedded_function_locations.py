import ast
import typing as T
from pathlib import Path

from groupy.utils.read_source import read_source

_FUNCTION_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def get_embedded_function_locations(source_root: Path, module_name: str) -> T.List[str]:
    # An embedded function is a function that is nested in another function. It
    # has no node, so it is located by the qualified name of its parents and
    # itself, e.g. create_report._format_lines.
    tree = ast.parse(read_source(source_root / module_name))
    result: T.List[str] = []
    for statement in tree.body:
        if isinstance(statement, _FUNCTION_DEFS):
            _collect(statement, statement.name, result)
        elif isinstance(statement, ast.ClassDef):
            for member in statement.body:
                if isinstance(member, _FUNCTION_DEFS):
                    _collect(member, f"{statement.name}.{member.name}", result)
    return result


def _collect(function_def: ast.AST, location: str, result: T.List[str]) -> None:
    for nested_def in _find_nested_function_defs(function_def):
        nested_location = f"{location}.{nested_def.name}"
        result.append(nested_location)
        _collect(nested_def, nested_location, result)


def _find_nested_function_defs(parent: ast.AST) -> T.List[ast.AST]:
    # The functions in the body of the parent (also in its if, for, try, ...
    # blocks), but not the ones in the bodies of those functions
    found = []
    for child in ast.iter_child_nodes(parent):
        if isinstance(child, _FUNCTION_DEFS):
            found.append(child)
        elif not isinstance(child, ast.ClassDef):
            found += _find_nested_function_defs(child)
    return found
