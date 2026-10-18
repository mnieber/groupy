import typing as T
from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field


def set_local_term(
    source_root: Path,
    module_name: str,
    location: str,
    local_term: str,
    description: T.Optional[str],
) -> None:
    def _edit(node):
        check_has_field(node, "local_terms")
        node.local_terms[local_term] = description

    edit_node(source_root, module_name, location, _edit)
