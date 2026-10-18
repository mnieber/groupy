import typing as T
from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.variable_node import VariableNode
from groupy.nodes.rules.check_node_has_field import check_node_has_field
from groupy.nodes.utils.exceptions import InvalidValueError


CODE_UNIT_TYPES_BY_NODE_TYPE = {
    FunctionNode: ("action", "rule", "util", "entrypoint"),
    ClassNode: ("model", "schema", "enum", "exception", "policy", "other"),
    VariableNode: ("constant", "setting"),
}


def set_code_unit_type(
    source_root: Path, module_name: str, location: str, code_unit_type: T.Optional[str]
) -> None:
    def _edit(node):
        check_node_has_field(node, "code_unit_type")
        code_unit_types = CODE_UNIT_TYPES_BY_NODE_TYPE[type(node)]
        if code_unit_type is not None and code_unit_type not in code_unit_types:
            raise InvalidValueError(
                f"The code unit type of {node.name} must be one of "
                f"{', '.join(code_unit_types)}, not {code_unit_type}"
            )
        node.code_unit_type = code_unit_type

    edit_node(source_root, module_name, location, _edit)
