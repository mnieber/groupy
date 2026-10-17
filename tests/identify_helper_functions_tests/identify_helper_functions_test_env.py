import typing as T

from groupy.call_graph.actions.build_call_graph import build_call_graph
from groupy.call_graph.models.call_graph import CallGraph
from groupy.call_graph.rules.load_call_graph import load_call_graph
from groupy.functions.actions.mark_helper_candidates import mark_helper_candidates
from groupy.functions.actions.move_function_to_parent import (
    move_function_to_parent,
)
from groupy.functions.actions.rename_helper_functions import (
    rename_helper_functions,
)
from groupy.nodes.models.module_node import ModuleNode
from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

__all__ = ["Context", "TestEnv"]

RFA_ID = "identify-helper-functions/group-1/chunk-1"


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the identify-helper-functions stage. The target code
    (in the src dir) has the modules of the base env plus the modules that
    the test adds. With the simple grouping strategy and large sizes, all
    modules are in the chunk group-1/chunk-1."""

    def __init__(self, context: Context):
        self.call_graph: CallGraph = None
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
        call_graph_path = self.repo_dir / ".groupy" / "call-graph.yaml"
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
        rename_helper_functions(
            self.source_root, module_names, self.refactoring_policy()
        )

    # Queries (for use in asserts)

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
