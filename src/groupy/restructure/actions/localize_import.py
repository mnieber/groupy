import ast
from pathlib import Path

from groupy.utils.get_dotted_name import get_dotted_name


def localize_import(
    source_root: Path,
    module_name: str,
    class_name: str,
    method_name: str,
    function_name: str,
    target_module_name: str,
) -> None:
    # Replaces the module-level import of the function (that the move added) by an
    # import inside the method, because the module of the function typically
    # imports the class (which would be a circular import)
    path = source_root / module_name
    dotted_name = get_dotted_name(target_module_name)
    lines = path.read_text().splitlines(keepends=True)

    # Remove the module-level import
    for statement in ast.parse("".join(lines)).body:
        if (
            isinstance(statement, ast.ImportFrom)
            and statement.module == dotted_name
            and any(alias.name == function_name for alias in statement.names)
        ):
            other_names = [
                alias for alias in statement.names if alias.name != function_name
            ]
            replacement = (
                [ast.unparse(ast.ImportFrom(dotted_name, other_names, 0)) + "\n"]
                if other_names
                else []
            )
            lines[statement.lineno - 1 : statement.end_lineno] = replacement
            break

    # Add the import as the first statement of the method
    tree = ast.parse("".join(lines))
    class_def = next(
        statement
        for statement in tree.body
        if isinstance(statement, ast.ClassDef) and statement.name == class_name
    )
    method_def = next(
        statement
        for statement in class_def.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name == method_name
    )
    first_line = lines[method_def.body[0].lineno - 1]
    indent = first_line[: len(first_line) - len(first_line.lstrip())]
    lines.insert(
        method_def.body[0].lineno - 1,
        f"{indent}from {dotted_name} import {function_name}\n",
    )
    path.write_text("".join(lines))
