from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_entry, check_has_field


def remove_step_to_move_to_caller(
    source_root: Path, module_name: str, location: str, step: str
) -> None:
    def _edit(node):
        check_has_field(node, "steps_to_move_to_caller")
        check_has_entry(node.steps_to_move_to_caller, step, "steps to move to caller")
        node.steps_to_move_to_caller.remove(step)

    edit_node(source_root, module_name, location, _edit)
