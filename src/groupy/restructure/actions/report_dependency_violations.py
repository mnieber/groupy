from pathlib import Path

from groupy.call_graph.actions.build_call_graph import build_call_graph
from groupy.call_graph.rules.load_call_graph import load_call_graph
from groupy.restructure.rules.find_dependency_violations import (
    find_dependency_violations,
)


def report_dependency_violations(source_root: Path, call_graph_path: Path) -> None:
    # The violations do not block the stage, because the developer may accept them
    build_call_graph(source_root, call_graph_path)
    violations = find_dependency_violations(
        source_root, load_call_graph(call_graph_path)
    )
    if not violations:
        print("The proposed code structure follows the dependency direction.")
        return
    print("The proposed code structure has dependency violations:")
    for violation in violations:
        print(violation)
