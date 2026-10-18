import typing as T
from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field


def set_rename_to(
    source_root: Path, module_name: str, location: str, new_name: T.Optional[str]
) -> None:
    def _edit(node):
        check_has_field(node, "rename_to")
        node.rename_to = new_name

    edit_node(source_root, module_name, location, _edit)
