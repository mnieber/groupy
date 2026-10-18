import ast
import re


def get_symbol_offset(text: str, node: ast.AST, name: str) -> int:
    # Returns the (character) offset of the name in the definition node
    lines = text.splitlines(keepends=True)
    line_start = sum(len(line) for line in lines[: node.lineno - 1])
    line = lines[node.lineno - 1]
    col = len(line.encode("utf-8")[: node.col_offset].decode("utf-8"))

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        # The name follows the def or class keyword (after the decorators)
        keyword = "class" if isinstance(node, ast.ClassDef) else "def"
        pattern = re.compile(rf"\b{keyword}\s+({re.escape(name)})\b")
        match = pattern.search(text, line_start + col)
        return match.start(1)
    if isinstance(node, ast.Attribute):
        end_line_start = sum(len(each) for each in lines[: node.end_lineno - 1])
        end_line = lines[node.end_lineno - 1]
        end_col = len(end_line.encode("utf-8")[: node.end_col_offset].decode("utf-8"))
        return end_line_start + end_col - len(name)
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return text.index(name, line_start + col)
    return line_start + col
