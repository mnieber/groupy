from pathlib import Path

from groupy.nodes.actions.save_module_node import save_module_node
from groupy.nodes.rules.get_module_node_file_path import get_module_node_file_path
from groupy.nodes.rules.load_module_node import load_module_node


def move_module_node_file(
    source_root: Path, module_name: str, new_module_name: str
) -> None:
    # The node file moves with its module, and its rename_to is cleared
    node_file_path = get_module_node_file_path(source_root, module_name)
    module_node = load_module_node(node_file_path)
    module_node.name = new_module_name
    module_node.rename_to = None
    save_module_node(
        module_node, get_module_node_file_path(source_root, new_module_name)
    )
    node_file_path.unlink()
