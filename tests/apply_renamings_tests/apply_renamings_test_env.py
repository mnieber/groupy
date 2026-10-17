import typing as T

from breaker.nodes.models.module_node import ModuleNode
from breaker.nodes.rules.load_module_node import load_module_node
from breaker_next_tests.breaker_next_test_env import Context
from breaker_next_tests.breaker_next_test_env import TestEnv as BreakerNextTestEnv

__all__ = ["Context", "TestEnv"]

STAGE = "apply-renamings"


class TestEnv(BreakerNextTestEnv):
    """A TestEnv for the apply-renamings stage. The target code (in the src
    dir) has the modules of the base env plus the modules that the test adds.
    With the simple grouping strategy and large sizes, all modules are in the
    chunk group-1/chunk-1."""

    def __init__(self, context: Context):
        self.source_root = context.repo_dir / "src"
        self.module_node: ModuleNode = None
        super().__init__(context)

    # Actions

    def create_session_at_apply_renamings(self, modules: T.Dict[str, str]) -> None:
        """Creates a session for the target code with the added modules, whose
        next stage is apply-renamings."""
        self.create_session(
            modules,
            grouping_strategy="simple",
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.set_next_stage(STAGE)

    def edit_node_file(
        self, action: T.Callable, module_name: str, location: str, *args
    ) -> None:
        """Runs the node file edit (e.g. set_renaming) on the node at the
        location, as the earlier stages or the developer would."""
        action(self.source_root, module_name, location, *args)

    def load_module_node(self, module_name: str) -> None:
        self.module_node = load_module_node(
            self.source_root / f"{module_name}.breaker.yaml"
        )

    # Queries (for use in asserts)

    def read_module(self, module_name: str) -> str:
        return (self.source_root / module_name).read_text()

    def names(self, nodes: T.List[T.Any]) -> T.List[str]:
        return [node.name for node in nodes]

    def function_node(self, location: str):
        """Returns the function node or method node at the location (e.g.
        `create_book` or `Book.__init__`)."""
        if "." in location:
            class_name, method_name = location.split(".")
            return _find_by_name(self.class_node(class_name).method_nodes, method_name)
        return _find_by_name(self.module_node.function_nodes, location)

    def class_node(self, name: str):
        return _find_by_name(self.module_node.class_nodes, name)


def _find_by_name(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]
