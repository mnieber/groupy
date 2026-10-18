import typing as T
from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field


def set_concept(
    source_root: Path,
    module_name: str,
    location: str,
    concept: str,
    description: T.Optional[str],
) -> None:
    def _edit(node):
        check_has_field(node, "concepts")
        node.concepts[concept] = description

    edit_node(source_root, module_name, location, _edit)
