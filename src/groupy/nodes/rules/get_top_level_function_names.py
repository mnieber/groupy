import ast
import typing as T
from pathlib import Path


def get_top_level_function_names(source_root: Path, module_name: str) -> T.List[str]:
    tree = ast.parse((source_root / module_name).read_text())
    return [
        statement.name
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
