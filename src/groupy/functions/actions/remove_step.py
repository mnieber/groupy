from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field, check_index


def remove_step(source_root: Path, module_name: str, location: str, index: int) -> None:
    def _edit(node):
        check_has_field(node, "steps")
        check_index(node.steps, index)
        old_step = node.steps.pop(index)

        # A step that is proposed to move is removed along with it
        node.steps_to_move_to_caller = [
            step_to_move
            for step_to_move in node.steps_to_move_to_caller
            if step_to_move != old_step
        ]

    edit_node(source_root, module_name, location, _edit)
