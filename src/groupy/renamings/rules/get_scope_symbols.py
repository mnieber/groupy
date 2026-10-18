import ast
import typing as T

_FUNCTION_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def get_scope_symbols(scope_def: ast.AST) -> T.Dict[str, ast.AST]:
    # Maps each symbol that is defined in the scope onto the AST node of its first
    # definition: top-level names for a module, methods and attributes for a
    # class, and parameters, local variables and nested functions for a function
    if isinstance(scope_def, ast.Module):
        return _get_module_symbols(scope_def)
    if isinstance(scope_def, ast.ClassDef):
        return _get_class_symbols(scope_def)
    return _get_function_symbols(scope_def)


def _add(symbols: T.Dict[str, ast.AST], name: str, node: ast.AST) -> None:
    symbols.setdefault(name, node)


def _get_module_symbols(tree: ast.Module) -> T.Dict[str, ast.AST]:
    symbols: T.Dict[str, ast.AST] = {}
    for statement in tree.body:
        if isinstance(statement, (*_FUNCTION_DEFS, ast.ClassDef)):
            _add(symbols, statement.name, statement)
        elif isinstance(statement, (ast.Import, ast.ImportFrom)):
            for alias in statement.names:
                _add(symbols, (alias.asname or alias.name).split(".")[0], statement)
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
            )
            for target in targets:
                for node in ast.walk(target):
                    if isinstance(node, ast.Name):
                        _add(symbols, node.id, node)
    return symbols


def _get_class_symbols(class_def: ast.ClassDef) -> T.Dict[str, ast.AST]:
    symbols: T.Dict[str, ast.AST] = {}
    for statement in class_def.body:
        if isinstance(statement, _FUNCTION_DEFS):
            _add(symbols, statement.name, statement)
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
            )
            for target in targets:
                if isinstance(target, ast.Name):
                    _add(symbols, target.id, target)

    # Attributes that the methods assign to self
    for statement in class_def.body:
        if isinstance(statement, _FUNCTION_DEFS) and statement.args.args:
            self_name = statement.args.args[0].arg
            for node in ast.walk(statement):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.ctx, ast.Store)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == self_name
                ):
                    _add(symbols, node.attr, node)
    return symbols


def _get_function_symbols(function_def: ast.AST) -> T.Dict[str, ast.AST]:
    symbols: T.Dict[str, ast.AST] = {}
    args = function_def.args
    for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
        _add(symbols, arg.arg, arg)
    for arg in (args.vararg, args.kwarg):
        if arg is not None:
            _add(symbols, arg.arg, arg)
    for node in ast.walk(function_def):
        if node is function_def:
            continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            _add(symbols, node.id, node)
        elif isinstance(node, (*_FUNCTION_DEFS, ast.ClassDef)):
            _add(symbols, node.name, node)
    return symbols
