from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field


def set_abbreviation(
    source_root: Path,
    module_name: str,
    location: str,
    term: str,
    abbreviation: str,
) -> None:
    def _edit(node):
        check_has_field(node, "abbreviations")
        node.abbreviations[term] = abbreviation

    edit_node(source_root, module_name, location, _edit)
