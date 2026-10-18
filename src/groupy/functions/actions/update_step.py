from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.rules.check_index import check_index
from groupy.nodes.rules.check_node_has_field import check_node_has_field


def update_step(
    source_root: Path, module_name: str, location: str, index: int, step: str
) -> None:
    def _edit(node):
        check_node_has_field(node, "steps")
        check_index(node.steps, index)
        old_step = node.steps[index]
        node.steps[index] = step

        # A step that is proposed to move is updated along with it
        node.steps_to_move_to_caller = [
            step if step_to_move == old_step else step_to_move
            for step_to_move in node.steps_to_move_to_caller
        ]

    edit_node(source_root, module_name, location, _edit)
