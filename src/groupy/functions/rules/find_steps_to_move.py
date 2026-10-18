import typing as T
from pathlib import Path

from groupy.functions.rules.get_function_locations import get_function_locations


def find_steps_to_move(
    source_root: Path, module_names: T.List[str]
) -> T.List[T.Tuple[str, str, str]]:
    # Returns the (node location, source location, step) triples of the steps that
    # are proposed to move, sorted by location and in the order of the steps
    result = []
    for node_location, source_location, node in get_function_locations(
        source_root, module_names
    ):
        for step in node.steps_to_move_to_caller:
            result.append((node_location, source_location, step))
    return sorted(result, key=lambda item: item[0])
