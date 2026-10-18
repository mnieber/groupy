import typing as T
from pathlib import Path

from groupy.nodes.actions.edit_node import edit_node
from groupy.nodes.utils.checks import check_has_field, check_index


def add_step(
    source_root: Path,
    module_name: str,
    location: str,
    step: str,
    index: T.Optional[int] = None,
) -> None:
    # Without an index, the step is added at the end
    def _edit(node):
        check_has_field(node, "steps")
        step_index = len(node.steps) if index is None else index
        check_index(node.steps, step_index, allow_end=True)
        node.steps.insert(step_index, step)

    edit_node(source_root, module_name, location, _edit)
