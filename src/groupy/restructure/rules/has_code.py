import ast
from groupy.utils.read_source import read_source
from pathlib import Path


def has_code(source_root: Path, module_name: str) -> bool:
    # Imports, a docstring and pass are not code
    for statement in ast.parse(read_source(source_root / module_name)).body:
        if isinstance(statement, (ast.Import, ast.ImportFrom, ast.Pass)):
            continue
        if isinstance(statement, ast.Expr) and isinstance(
            statement.value, ast.Constant
        ):
            continue
        return True
    return False
