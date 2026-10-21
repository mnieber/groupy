import typing as T
from pathlib import Path

from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def find_passive_renamings(
    source_root: Path, passive_module_names: T.List[str]
) -> T.List[str]:
    # Returns a conflict line per node with a renaming in a passive file. The
    # rename_to of a module is not a renaming (it belongs to the code restructure).
    conflicts = []
    for module_name in passive_module_names:
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        for located_node in get_located_nodes(module_node):
            node = located_node.node
            is_module = located_node.location == "@module"
            # A variable node has no renamings
            renamings = getattr(node, "renamings", {})
            if renamings or (node.rename_to and not is_module):
                conflicts.append(
                    f"{module_name}:{located_node.location}: is in a passive file"
                )
    return conflicts
