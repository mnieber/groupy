from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def add_responsibility(
    source_root: Path, module_name: str, location: str, responsibility: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "responsibilities")
        node.responsibilities.append(responsibility)

    edit_node(source_root, module_name, location, _edit)
