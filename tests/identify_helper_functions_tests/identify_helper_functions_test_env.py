import typing as T

from breaker.call_graph.actions.build_call_graph import build_call_graph
from breaker.call_graph.models.call_graph import CallGraph
from breaker.call_graph.rules.load_call_graph import load_call_graph
from breaker.functions.actions.mark_helper_candidates import mark_helper_candidates
from breaker.functions.actions.move_function_to_parent import (
    move_function_to_parent,
)
from breaker.functions.actions.rename_helper_functions import (
    rename_helper_functions,
)
from breaker.nodes.models.module_node import ModuleNode
from breaker.nodes.rules.load_module_node import load_module_node
from breaker_next_tests.breaker_next_test_env import Context
from breaker_next_tests.breaker_next_test_env import TestEnv as BreakerNextTestEnv

__all__ = ["Context", "TestEnv"]

RFA_ID = "identify-helper-functions/group-1/chunk-1"


class TestEnv(BreakerNextTestEnv):
    """A TestEnv for the identify-helper-functions stage. The target code
    (in the src dir) has the modules of the base env plus the modules that
    the test adds. With the simple grouping strategy and large sizes, all
    modules are in the chunk group-1/chunk-1."""

    def __init__(self, context: Context):
        self.source_root = context.repo_dir / "src"
        self.call_graph: CallGraph = None
        self.module_node: ModuleNode = None
        super().__init__(context)

    # Actions

    def create_session_with_modules(self, modules: T.Dict[str, str]) -> None:
        """Creates a session (that uses the fake RFA policy) for the target
        code with the added modules, where all modules are in one chunk."""
        self.create_session(
            modules,
            grouping_strategy="simple",
            max_group_lines=10000,
            max_chunk_lines=10000,
        )

    def build_call_graph(self) -> None:
        """Builds the call graph of the target code into env.call_graph."""
        call_graph_path = self.repo_dir / ".breaker" / "call-graph.yaml"
        build_call_graph(self.source_root, call_graph_path)
        self.call_graph = load_call_graph(call_graph_path)

    def mark_helper_candidates(self, module_names: T.List[str]) -> None:
        mark_helper_candidates(self.source_root, self.call_graph, module_names)

    def move_function_to_parent(
        self, module_name: str, function_location: str, parent_location: str
    ) -> None:
        move_function_to_parent(
            self.source_root, module_name, function_location, parent_location
        )

    def rename_helper_functions(self, module_names: T.List[str]) -> None:
        rename_helper_functions(self.source_root, module_names)

    def catch_error(self, env_action: T.Callable, *args, **kwargs) -> None:
        """Runs the env action and stores the exception it is expected to
        raise in env.error."""
        self.error = None
        try:
            env_action(*args, **kwargs)
        except Exception as error:
            self.error = error

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
        """Returns the function node at the location, where the location is
        the qualified name of the node in the node file (e.g. `Book.save`, or
        `create_report._format_lines` for a helper function node)."""
        first_name, *other_names = location.split(".")
        class_matches = [
            node for node in self.module_node.class_nodes if node.name == first_name
        ]
        if class_matches:
            node = _find_by_name(class_matches[0].method_nodes, other_names.pop(0))
        else:
            node = _find_by_name(self.module_node.function_nodes, first_name)
        for name in other_names:
            node = _find_by_name(node.helper_function_nodes, name)
        return node

    def helper_names(self, location: str) -> T.List[str]:
        return self.names(self.function_node(location).helper_function_nodes)

    def helper_candidates(self) -> T.Set[str]:
        """Returns the locations of the function nodes (also the method nodes
        and helper function nodes) of env.module_node that are marked as
        helper candidates."""
        return {
            location
            for location, node in _all_function_nodes(self.module_node)
            if node.is_helper_candidate
        }

    def callers_in_context(self, rfa_id: str, location: str) -> T.Set[T.Tuple]:
        """Returns the (caller, scope, is_certain) triples of the function view
        at the location, in the call graph view in the context of the RFA."""
        return {
            (call.location, call.scope, call.is_certain)
            for call in self.function_view_in_context(rfa_id, location).callers
        }


def _find_by_name(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]


def _all_function_nodes(module_node: ModuleNode) -> T.Iterator[T.Tuple[str, T.Any]]:
    """Yields the (location, node) pairs of all function nodes in the module
    node, including the method nodes and the helper function nodes."""

    def with_helpers(prefix: str, nodes: T.List[T.Any]):
        for node in nodes:
            location = f"{prefix}{node.name}"
            yield location, node
            yield from with_helpers(f"{location}.", node.helper_function_nodes)

    yield from with_helpers("", module_node.function_nodes)
    for class_node in module_node.class_nodes:
        yield from with_helpers(f"{class_node.name}.", class_node.method_nodes)
