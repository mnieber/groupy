import ast
import typing as T

_FUNCTION_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def find_scope_def(tree: ast.Module, scope_location: str) -> T.Optional[ast.AST]:
    # Returns the module (for @module), the class or the function of the scope.
    # The scope of a helper function (e.g. create_book._validate) is a top-level
    # function in the source.
    if scope_location == "@module":
        return tree
    parts = scope_location.split(".")
    classes = {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, ast.ClassDef)
    }
    if parts[0] in classes and len(parts) <= 2:
        class_def = classes[parts[0]]
        if len(parts) == 1:
            return class_def
        return _find_function(class_def.body, parts[1])
    return _find_function(tree.body, parts[-1])


def _find_function(body: T.List[ast.stmt], name: str) -> T.Optional[ast.AST]:
    for statement in body:
        if isinstance(statement, _FUNCTION_DEFS) and statement.name == name:
            return statement
    return None
