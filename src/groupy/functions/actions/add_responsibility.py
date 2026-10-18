from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field


def add_responsibility(
    source_root: Path, module_name: str, location: str, responsibility: str
) -> None:
    def _edit(node):
        check_has_field(node, "responsibilities")
        node.responsibilities.append(responsibility)

    edit_node(source_root, module_name, location, _edit)
