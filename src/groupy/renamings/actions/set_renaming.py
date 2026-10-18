from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_node_has_field import check_node_has_field
from groupy.nodes.utils.exceptions import InvalidValueError


def set_renaming(
    source_root: Path, module_name: str, location: str, name: str, new_name: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "renamings")
        if new_name == name:
            raise InvalidValueError(f"The renaming of {name} does not change the name")
        # The node itself is renamed with rename_to
        if name == node.name:
            raise InvalidValueError(
                f"Use rename_to to rename {name}, instead of its renamings"
            )
        node.renamings[name] = new_name

    edit_node(source_root, module_name, location, _edit)
