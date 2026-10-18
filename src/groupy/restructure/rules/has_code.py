import ast
from pathlib import Path


def has_code(source_root: Path, module_name: str) -> bool:
    # Imports, a docstring and pass are not code
    for statement in ast.parse((source_root / module_name).read_text()).body:
        if isinstance(statement, (ast.Import, ast.ImportFrom, ast.Pass)):
            continue
        if isinstance(statement, ast.Expr) and isinstance(
            statement.value, ast.Constant
        ):
            continue
        return True
    return False
