import ast
from pathlib import Path

from groupy.claude_requests.models.rfr import Rfr
from groupy.claude_requests.policies.rfr_policy import RfrPolicy
from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.get_top_level_function_names import get_top_level_function_names
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.renamings.rules.find_scope_def import find_scope_def

PROMPT = """\
Extract a part of the function at the location in the module into the new top-level
function new_name (also when the function is a method), as described in the
description, and call the new function from the original function. Only edit the
source: do not call commit_refactoring.
"""


def extract_method(
    source_root: Path,
    module_name: str,
    location: str,
    new_name: str,
    description: str,
    rfr_policy: RfrPolicy,
) -> None:
    old_function_names = get_top_level_function_names(source_root, module_name)
    rfr_policy.run(
        Rfr(
            id=f"extract_method/{module_name}:{location}/{new_name}",
            prompt=PROMPT,
            context={
                "module_name": module_name,
                "location": location,
                "new_name": new_name,
                "description": description,
            },
        )
    )

    # Check that Claude added the new function, and kept the original one
    function_names = get_top_level_function_names(source_root, module_name)
    if new_name in old_function_names or new_name not in function_names:
        raise ExtractMethodFailedError(
            f"The extraction did not add the function {new_name} to {module_name}"
        )
    tree = ast.parse((source_root / module_name).read_text())
    if find_scope_def(tree, location) is None:
        raise ExtractMethodFailedError(
            f"The extraction of {new_name} removed {location} from {module_name}"
        )

    # Add the node of the new function, in source order
    node_file_path = get_module_node_file_path(source_root, module_name)
    module_node = load_module_node(node_file_path)
    following_names = function_names[function_names.index(new_name) + 1 :]
    new_node = FunctionNode(name=new_name)
    for index, node in enumerate(module_node.function_nodes):
        if node.name in following_names:
            module_node.function_nodes.insert(index, new_node)
            break
    else:
        module_node.function_nodes.append(new_node)
    save_module_node(module_node, node_file_path)


class ExtractMethodFailedError(Exception):
    pass
