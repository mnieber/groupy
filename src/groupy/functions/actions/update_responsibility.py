from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_index import check_index
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def update_responsibility(
    source_root: Path, module_name: str, location: str, index: int, responsibility: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "responsibilities")
        check_index(node.responsibilities, index)
        node.responsibilities[index] = responsibility

    edit_node(source_root, module_name, location, _edit)
