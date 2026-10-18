from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_has_entry import check_has_entry
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def remove_concept(
    source_root: Path, module_name: str, location: str, concept: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "concepts")
        check_has_entry(node.concepts, concept, "concepts")
        del node.concepts[concept]

    edit_node(source_root, module_name, location, _edit)
