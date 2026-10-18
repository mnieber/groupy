import ast
import copy
import typing as T

from groupy.utils.to_snake_case import to_snake_case


def create_delegation(
    text: str, class_name: str, method_name: str, function_name: str
) -> str:
    # Returns the text of the module where the method delegates to a new top-level
    # function with the body of the method. In the function, self is replaced by a
    # parameter that is named after the class.
    tree = ast.parse(text)
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
    lines = text.splitlines(keepends=True)
    self_name = method_def.args.args[0].arg
    parameter_name = to_snake_case(class_name)

    # The body of the new function, with self replaced
    body_start = method_def.body[0].lineno
    body_lines = lines[body_start - 1 : method_def.end_lineno]
    replacements = [
        node
        for node in ast.walk(method_def)
        if isinstance(node, ast.Name)
        and node.id == self_name
        and node.lineno >= body_start
    ]
    for node in sorted(
        replacements, key=lambda node: (node.lineno, node.col_offset), reverse=True
    ):
        index = node.lineno - body_start
        line = body_lines[index].encode("utf-8")
        body_lines[index] = (
            line[: node.col_offset]
            + parameter_name.encode("utf-8")
            + line[node.end_col_offset :]
        ).decode("utf-8")
    body = _reindent(body_lines, "    ")

    # The signature of the new function, and the call in the method
    function_args = copy.deepcopy(method_def.args)
    function_args.args[0].arg = parameter_name
    is_async = isinstance(method_def, ast.AsyncFunctionDef)
    function_text = (
        f"{'async ' if is_async else ''}def {function_name}"
        f"({ast.unparse(function_args)}):\n{body}"
    )
    call = f"{function_name}({', '.join([self_name, *_get_call_args(method_def)])})"
    method_indent = _get_indent(body_lines[0]) if body_lines else "        "
    method_body = f"{method_indent}return {'await ' if is_async else ''}{call}\n"

    # Replace the body of the method, and add the function after the class
    new_lines = (
        lines[: body_start - 1]
        + [method_body]
        + lines[method_def.end_lineno : class_def.end_lineno]
    )
    rest = lines[class_def.end_lineno :]
    return "".join(new_lines) + f"\n\n{function_text}" + "".join(rest)


def _get_call_args(method_def) -> T.List[str]:
    args = method_def.args
    result = [arg.arg for arg in [*args.posonlyargs, *args.args][1:]]
    if args.vararg:
        result.append(f"*{args.vararg.arg}")
    result += [f"{arg.arg}={arg.arg}" for arg in args.kwonlyargs]
    if args.kwarg:
        result.append(f"**{args.kwarg.arg}")
    return result


def _get_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _reindent(lines: T.List[str], indent: str) -> str:
    # Dedents the lines, and indents them with the indent
    non_empty = [line for line in lines if line.strip()]
    common = min(len(_get_indent(line)) for line in non_empty) if non_empty else 0
    return "".join(indent + line[common:] if line.strip() else "\n" for line in lines)
