from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_entry, check_has_field


def remove_alias(
    source_root: Path, module_name: str, location: str, name: str, alias: str
) -> None:
    def _edit(node):
        check_has_field(node, "aliases")
        check_has_entry(node.aliases.get(name, []), alias, f"aliases of {name}")
        node.aliases[name].remove(alias)
        if not node.aliases[name]:
            del node.aliases[name]

    edit_node(source_root, module_name, location, _edit)
