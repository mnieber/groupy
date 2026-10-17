import typing as T

from breaker.claude_requests.models.callback import Callback
from breaker.claude_requests.models.rfr import Rfr
from breaker.nodes.models.module_node import ModuleNode
from breaker.nodes.rules.load_module_node import load_module_node
from breaker_next_tests.breaker_next_test_env import Context
from breaker_next_tests.breaker_next_test_env import TestEnv as BreakerNextTestEnv

__all__ = ["Context", "TestEnv"]

STAGE = "extract-methods"


class TestEnv(BreakerNextTestEnv):
    """A TestEnv for the extract-methods stage. The target code (in the src
    dir) has the modules of the base env plus the modules that the test
    adds."""

    def __init__(self, context: Context):
        self.source_root = context.repo_dir / "src"
        self.module_node: ModuleNode = None
        super().__init__(context)

    # Actions

    def create_session_at_extract_methods(
        self, modules: T.Dict[str, str], grouping_strategy: str = "simple"
    ) -> None:
        """Creates a session for the target code with the added modules, whose
        next stage is extract-methods. With the simple grouping strategy, all
        modules are in the chunk group-1/chunk-1. With the package grouping
        strategy, the modules of myapp/chapters are in the chunk
        group-2/chunk-1."""
        self.create_session(
            modules,
            grouping_strategy=grouping_strategy,
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.set_next_stage(STAGE)

    def edit_node_file(
        self, action: T.Callable, module_name: str, location: str, *args
    ) -> None:
        """Runs the node file edit (e.g. set_extract_method_priority) on the
        node at the location, as the earlier stages would."""
        action(self.source_root, module_name, location, *args)

    def load_module_node(self, module_name: str) -> None:
        self.module_node = load_module_node(
            self.source_root / f"{module_name}.breaker.yaml"
        )

    # Queries (for use in asserts)

    def rfr(self, rfr_id: str) -> Rfr:
        matches = [rfr for rfr in self.rfr_policy().requests if rfr.id == rfr_id]
        assert len(matches) == 1, f"Expected one RFR with the id {rfr_id}"
        return matches[0]

    def read_module(self, module_name: str) -> str:
        return (self.source_root / module_name).read_text()

    def names(self, nodes: T.List[T.Any]) -> T.List[str]:
        return [node.name for node in nodes]

    def function_node(self, location: str):
        """Returns the function node at the location, where the location is
        the qualified name of the node in the node file (e.g. `create_report`
        or `create_report._format_stats`)."""
        first_name, *other_names = location.split(".")
        node = _find_by_name(self.module_node.function_nodes, first_name)
        for name in other_names:
            node = _find_by_name(node.helper_function_nodes, name)
        return node


def commit_messages(callbacks: T.List[Callback]) -> T.List[str]:
    """Returns the messages of the commits that Breaker makes after running
    the callbacks."""
    return [f"{STAGE}: {callback.name}" for callback in callbacks]


def _find_by_name(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]
