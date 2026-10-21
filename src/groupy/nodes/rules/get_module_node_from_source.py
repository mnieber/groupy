import ast
import typing as T
from pathlib import Path

from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.models.variable_node import VariableNode
from groupy.utils.read_source import read_source

_FUNCTION_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def get_module_node_from_source(source_root: Path, module_name: str) -> ModuleNode:
    text = read_source(source_root / module_name)
    tree = ast.parse(text)

    # Functions that are nested in the code have no node of their own
    return ModuleNode(
        name=module_name,
        line_count=len(text.splitlines()),
        function_nodes=[
            FunctionNode(name=statement.name)
            for statement in tree.body
            if isinstance(statement, _FUNCTION_DEFS)
        ],
        class_nodes=[
            _create_class_node(statement)
            for statement in tree.body
            if isinstance(statement, ast.ClassDef)
        ],
        variable_nodes=[VariableNode(name=name) for name in _get_variable_names(tree)],
    )


def _create_class_node(class_def: ast.ClassDef) -> ClassNode:
    return ClassNode(
        name=class_def.name,
        method_nodes=[
            FunctionNode(name=statement.name)
            for statement in class_def.body
            if isinstance(statement, _FUNCTION_DEFS)
        ],
    )


def _get_variable_names(tree: ast.Module) -> T.List[str]:
    names = []
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
        else:
            continue

        # A tuple assignment assigns each of its names
        for target in targets:
            elements = target.elts if isinstance(target, ast.Tuple) else [target]
            for element in elements:
                if isinstance(element, ast.Name) and element.id not in names:
                    names.append(element.id)
    return names
