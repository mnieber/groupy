import ast
import typing as T

from groupy.nodes.utils.exceptions import NodeNotFoundError

_FUNCTION_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def find_function_def(
    tree: ast.Module, qualified_name: str
) -> T.Union[ast.FunctionDef, ast.AsyncFunctionDef]:
    # The qualified name is a top-level function (e.g. create_book) or a method
    # (e.g. Book.save)
    *class_names, name = qualified_name.split(".")
    body = tree.body
    for class_name in class_names:
        class_defs = [
            statement
            for statement in body
            if isinstance(statement, ast.ClassDef) and statement.name == class_name
        ]
        if not class_defs:
            raise NodeNotFoundError(f"There is no class {class_name}")
        body = class_defs[0].body
    for statement in body:
        if isinstance(statement, _FUNCTION_DEFS) and statement.name == name:
            return statement
    raise NodeNotFoundError(f"There is no function {qualified_name}")
