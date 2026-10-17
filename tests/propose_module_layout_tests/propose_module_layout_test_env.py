import typing as T

from groupy.nodes.models.package_node import PackageNode
from groupy.nodes.rules.load_package_node import load_package_node
from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

__all__ = ["Context", "TestEnv"]

STAGE = "propose-module-layout"


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the propose-module-layout stage. The target code (in the
    src dir) has the modules of the base env plus the modules that the test
    adds."""

    def __init__(self, context: Context):
        self.package_node: PackageNode = None
        super().__init__(context)

    # Actions

    def create_session_at_propose_module_layout(
        self, modules: T.Dict[str, str] = None
    ) -> None:
        """Creates a session for the target code with the added modules, whose
        next stage is propose-module-layout."""
        self.create_session(
            modules,
            grouping_strategy="package",
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.set_next_stage(STAGE)

    def load_root_package_node(self) -> None:
        """Loads the package node file of the target dir into
        env.package_node."""
        self.package_node = load_package_node(
            self.source_root / "package-node.groupy.yaml"
        )
