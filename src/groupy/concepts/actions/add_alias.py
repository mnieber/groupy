from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field


def add_alias(
    source_root: Path, module_name: str, location: str, name: str, alias: str
) -> None:
    def _edit(node):
        check_has_field(node, "aliases")
        aliases = node.aliases.setdefault(name, [])
        if alias not in aliases:
            aliases.append(alias)

    edit_node(source_root, module_name, location, _edit)
