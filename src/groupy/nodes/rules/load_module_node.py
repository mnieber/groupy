import typing as T
from pathlib import Path

import yaml
from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.models.variable_node import VariableNode


def load_module_node(node_file_path: Path) -> ModuleNode:
    data = yaml.safe_load(node_file_path.read_text())["module_node"] or {}
    return ModuleNode(
        **_with_descriptions(data, "concepts"),
        function_nodes=[
            _create_function_node(item) for item in data.get("function_nodes") or []
        ],
        class_nodes=[
            _create_class_node(item) for item in data.get("class_nodes") or []
        ],
        variable_nodes=[
            VariableNode(**item) for item in data.get("variable_nodes") or []
        ],
    )


def _create_function_node(data: T.Dict[str, T.Any]) -> FunctionNode:
    return FunctionNode(
        **_with_descriptions(data, "concepts", "local_terms"),
        helper_function_nodes=[
            _create_function_node(item)
            for item in data.get("helper_function_nodes") or []
        ],
    )


def _create_class_node(data: T.Dict[str, T.Any]) -> ClassNode:
    return ClassNode(
        **_with_descriptions(data, "concepts"),
        method_nodes=[
            _create_function_node(item) for item in data.get("method_nodes") or []
        ],
    )


def _with_descriptions(
    data: T.Dict[str, T.Any], *description_fields: str
) -> T.Dict[str, T.Any]:
    # Returns the scalar fields of a node, where an empty description is None
    nested_fields = ("function_nodes", "class_nodes", "variable_nodes")
    nested_fields += ("helper_function_nodes", "method_nodes")
    result = {
        key: value
        for key, value in data.items()
        if key not in nested_fields and value is not None
    }
    for field in description_fields:
        if field in result:
            result[field] = {
                term: description or None
                for term, description in (result[field] or {}).items()
            }
    return result
