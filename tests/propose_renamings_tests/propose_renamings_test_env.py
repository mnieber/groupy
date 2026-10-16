import typing as T

from breaker.claude_requests.models.callback import Callback
from breaker.nodes.models.module_node import ModuleNode
from breaker.nodes.rules.load_module_node import load_module_node
from breaker_next_tests.breaker_next_test_env import Context
from breaker_next_tests.breaker_next_test_env import TestEnv as BreakerNextTestEnv

__all__ = ["Context", "TestEnv"]

STAGE = "propose-renamings"

RFA_ID = "propose-renamings/group-1/chunk-1"

RETRY_RFA_ID = "propose-renamings/group-1/chunk-1/retry-1"


class TestEnv(BreakerNextTestEnv):
    """A TestEnv for the propose-renamings stage. The target code (in the src
    dir) has the modules of the base env plus the modules that the test adds.
    With the simple grouping strategy and large sizes, all modules are in the
    chunk group-1/chunk-1."""

    def __init__(self, context: Context):
        self.source_root = context.repo_dir / "src"
        self.module_node: ModuleNode = None
        super().__init__(context)

    # Actions

    def create_session_at_propose_renamings(
        self, modules: T.Dict[str, str], glossary_text: str = None
    ) -> None:
        """Creates a session (that uses the fake RFA policy) for the target
        code with the added modules, whose next stage is propose-renamings.
        If glossary_text is given, the target code has this glossary file."""
        self.create_session(
            modules,
            grouping_strategy="simple",
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        if glossary_text is not None:
            self.write_file("src/glossary.breaker.yaml", glossary_text)
        self.set_next_stage(STAGE)

    def load_module_node(self, module_name: str) -> None:
        self.module_node = load_module_node(
            self.source_root / f"{module_name}.breaker.yaml"
        )

    # Queries (for use in asserts)

    def read_module(self, module_name: str) -> str:
        return (self.source_root / module_name).read_text()

    def function_node(self, location: str):
        """Returns the function node or method node at the location (e.g.
        `create_book` or `Book.__init__`)."""
        if "." in location:
            class_name, method_name = location.split(".")
            return _find_by_name(self.class_node(class_name).method_nodes, method_name)
        return _find_by_name(self.module_node.function_nodes, location)

    def class_node(self, name: str):
        return _find_by_name(self.module_node.class_nodes, name)

    def variable_node(self, name: str):
        return _find_by_name(self.module_node.variable_nodes, name)


def commit_messages(callbacks: T.List[Callback]) -> T.List[str]:
    """Returns the messages of the commits that Breaker makes after running
    the callbacks."""
    return [f"{STAGE}: {callback.name}" for callback in callbacks]


def _find_by_name(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]
