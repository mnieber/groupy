import typing as T
from pathlib import Path

from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def find_passive_proposals(
    source_root: Path, passive_module_names: T.List[str]
) -> T.List[str]:
    # Returns a problem line per node with a proposal for the code restructure in a
    # passive file
    problems = []
    for module_name in passive_module_names:
        module_node = load_module_node(
            get_module_node_file_path(source_root, module_name)
        )
        for located_node in get_located_nodes(module_node):
            node = located_node.node
            if located_node.location == "@module":
                has_proposal = bool(node.rename_to)
            else:
                has_proposal = bool(node.code_unit_type or node.move_to_file)
            if has_proposal:
                problems.append(
                    f"{module_name}:{located_node.location}: is in a passive file"
                )
    return problems
