import typing as T
from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def set_rename_to(
    source_root: Path, module_name: str, location: str, new_name: T.Optional[str]
) -> None:
    def _edit(node):
        check_node_has_field(node, "rename_to")
        node.rename_to = new_name

    edit_node(source_root, module_name, location, _edit)
