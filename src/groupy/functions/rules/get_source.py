import ast
import textwrap
from pathlib import Path

from groupy.functions.rules.find_function_def import find_function_def
from groupy.nodes.utils.exceptions import NodeNotFoundError


def get_source(source_root: Path, location: str) -> str:
    # The location is <module>:<qualified name>. The source of a method is dedented.
    module_name, qualified_name = location.split(":", 1)
    module_path = source_root / module_name
    if not module_path.exists():
        raise NodeNotFoundError(f"There is no module {module_name}")
    text = module_path.read_text()
    function_def = find_function_def(ast.parse(text), qualified_name)
    first_line = min(
        [function_def.lineno]
        + [decorator.lineno for decorator in function_def.decorator_list]
    )
    lines = text.splitlines()[first_line - 1 : function_def.end_lineno]
    return textwrap.dedent("\n".join(lines) + "\n")
