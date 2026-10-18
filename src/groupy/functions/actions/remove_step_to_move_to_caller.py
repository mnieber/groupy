from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_has_entry import check_has_entry
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def remove_step_to_move_to_caller(
    source_root: Path, module_name: str, location: str, step: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "steps_to_move_to_caller")
        check_has_entry(node.steps_to_move_to_caller, step, "steps to move to caller")
        node.steps_to_move_to_caller.remove(step)

    edit_node(source_root, module_name, location, _edit)
