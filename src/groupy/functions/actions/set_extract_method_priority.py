from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_node_has_field import check_node_has_field
from groupy.nodes.utils.exceptions import InvalidValueError


EXTRACT_METHOD_PRIORITIES = ("high", "medium", "low", "n/a")


def set_extract_method_priority(
    source_root: Path, module_name: str, location: str, priority: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "extract_method_priority")
        if priority not in EXTRACT_METHOD_PRIORITIES:
            raise InvalidValueError(
                f"The extract-method priority {priority} is not one of "
                f"{', '.join(EXTRACT_METHOD_PRIORITIES)}"
            )
        node.extract_method_priority = priority

    edit_node(source_root, module_name, location, _edit)
