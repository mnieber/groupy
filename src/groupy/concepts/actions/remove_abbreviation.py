from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_entry, check_has_field


def remove_abbreviation(
    source_root: Path, module_name: str, location: str, term: str
) -> None:
    def _edit(node):
        check_has_field(node, "abbreviations")
        check_has_entry(node.abbreviations, term, "abbreviations")
        del node.abbreviations[term]

    edit_node(source_root, module_name, location, _edit)
