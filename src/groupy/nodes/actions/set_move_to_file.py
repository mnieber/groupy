import typing as T
from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def set_move_to_file(
    source_root: Path, module_name: str, location: str, move_to_file: T.Optional[str]
) -> None:
    def _edit(node):
        check_node_has_field(node, "move_to_file")
        node.move_to_file = move_to_file

    edit_node(source_root, module_name, location, _edit)
