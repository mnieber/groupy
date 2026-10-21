import ast
import typing as T
from groupy.utils.read_source import read_source
from pathlib import Path


def get_top_level_function_names(source_root: Path, module_name: str) -> T.List[str]:
    tree = ast.parse(read_source(source_root / module_name))
    return [
        statement.name
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
