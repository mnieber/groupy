from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_has_entry import check_has_entry
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def remove_alias(
    source_root: Path, module_name: str, location: str, name: str, alias: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "aliases")
        check_has_entry(node.aliases.get(name, []), alias, f"aliases of {name}")
        node.aliases[name].remove(alias)
        if not node.aliases[name]:
            del node.aliases[name]

    edit_node(source_root, module_name, location, _edit)
