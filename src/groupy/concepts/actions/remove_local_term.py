from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_has_entry import check_has_entry
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def remove_local_term(
    source_root: Path, module_name: str, location: str, local_term: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "local_terms")
        check_has_entry(node.local_terms, local_term, "local terms")
        del node.local_terms[local_term]

    edit_node(source_root, module_name, location, _edit)
