from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_entry, check_has_field


def remove_renaming(
    source_root: Path, module_name: str, location: str, name: str
) -> None:
    def _edit(node):
        check_has_field(node, "renamings")
        check_has_entry(node.renamings, name, "renamings")
        del node.renamings[name]

    edit_node(source_root, module_name, location, _edit)
