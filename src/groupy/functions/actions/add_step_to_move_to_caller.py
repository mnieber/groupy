from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field
from groupy.nodes.utils.exceptions import InvalidValueError


def add_step_to_move_to_caller(
    source_root: Path, module_name: str, location: str, step: str
) -> None:
    def _edit(node):
        check_has_field(node, "steps_to_move_to_caller")
        if step not in node.steps:
            raise InvalidValueError(f"{node.name} has no step {step}")

        # The steps to move are kept in the order of the steps
        steps_to_move = set(node.steps_to_move_to_caller) | {step}
        node.steps_to_move_to_caller = [
            each_step for each_step in node.steps if each_step in steps_to_move
        ]

    edit_node(source_root, module_name, location, _edit)
