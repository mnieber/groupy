from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field, check_index


def remove_responsibility(
    source_root: Path, module_name: str, location: str, index: int
) -> None:
    def _edit(node):
        check_has_field(node, "responsibilities")
        check_index(node.responsibilities, index)
        del node.responsibilities[index]

    edit_node(source_root, module_name, location, _edit)
