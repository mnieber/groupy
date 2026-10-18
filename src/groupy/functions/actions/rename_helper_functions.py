import typing as T
from pathlib import Path

from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_located_nodes import get_located_nodes
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.renamings.policies.refactoring_policy import RefactoringPolicy


def rename_helper_functions(
    source_root: Path,
    module_names: T.List[str],
    refactoring_policy: RefactoringPolicy,
) -> bool:
    # Renames the helper functions so that they start with an underscore, in the
    # source (including the call sites) and in the node file. Returns whether a
    # function was renamed.
    renamed = False
    for module_name in module_names:
        node_file_path = get_module_node_file_path(source_root, module_name)
        module_node = load_module_node(node_file_path)
        for located_node in get_located_nodes(module_node):
            node = located_node.node
            is_helper = isinstance(located_node.parent, FunctionNode)
            if is_helper and not node.name.startswith("_"):
                new_name = f"_{node.name}"
                refactoring_policy.rename_symbol(
                    source_root, module_name, "@module", node.name, new_name
                )
                node.name = new_name
                renamed = True
        save_module_node(module_node, node_file_path)
    return renamed
