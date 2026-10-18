import ast
import subprocess
import sys
import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

from groupy.concepts.models.glossary import Glossary
from groupy.concepts.rules.load_glossary import load_glossary
from groupy.package_nodes.models.package_node import PackageNode
from groupy.package_nodes.rules.get_package_node_file_path import (
    get_package_node_file_path,
)
from groupy.package_nodes.rules.load_package_node import load_package_node

__all__ = ["Context", "TestEnv"]


class TestEnv(GroupyNextTestEnv):
    """A TestEnv that runs the stages with the real Claude policies. The
    target code (in the src dir) only has the modules of the test, which are
    all in one chunk."""

    def __init__(self, context: Context):
        self.glossary: Glossary = None
        self.package_node: PackageNode = None
        self.remembered_behaviour: str = None
        super().__init__(context)

    # Actions

    def create_session_with_claude(
        self, modules: T.Dict[str, str], claude_model: str = "haiku"
    ) -> None:
        """Creates a git repo whose target code is the myapp package with the
        modules (a map from module name to text), with a config that uses the
        real Claude policies and the Claude model, and runs groupy init."""
        self.repo_dir.mkdir(parents=True)
        self.write_file("README.md", "# My app\n")
        self.write_file("src/myapp/__init__.py", "")
        for module_name, text in modules.items():
            self.write_file(f"src/{module_name}", text)
        self.run_git("init")
        self.run_git("config", "user.email", "test@example.com")
        self.run_git("config", "user.name", "Test")
        self.commit_all("initial commit")
        self.run_git("branch", "-M", "main")
        self.context.monkeypatch.chdir(self.repo_dir)

        config_lines = [
            "grouping_strategy: simple",
            "max_group_lines: 10000",
            "max_chunk_lines: 10000",
            f"claude_model: {claude_model}",
        ]
        self.write_file(".groupy/config.yaml", "\n".join(config_lines) + "\n")
        self.commit_all("add groupy config")
        self.run_groupy("init", "--target-dir=src")

    def edit_package_node_file(self, action: T.Callable, *args) -> None:
        """Runs the package node file edit (e.g. set_proposed_module), as the
        earlier stages or the developer would."""
        action(self.source_root, *args)

    def write_glossary(self, text: str) -> None:
        self.write_file("src/glossary.groupy.yaml", text)

    def remember_behaviour(self, module_name: str, expression: str) -> None:
        self.remembered_behaviour = self.behaviour(module_name, expression)

    def load_glossary(self) -> None:
        self.glossary = load_glossary(self.source_root / "glossary.groupy.yaml")

    def load_root_package_node(self) -> None:
        self.package_node = load_package_node(
            get_package_node_file_path(self.source_root, ".")
        )

    # Queries (for use in asserts)

    def behaviour(self, module_name: str, expression: str) -> str:
        """Evaluates the expression in a fresh Python process, after importing
        everything from the module, and returns what it prints (including the
        repr of the result, and any error)."""
        dotted_name = module_name.removesuffix(".py").replace("/", ".")
        code = (
            "import sys\n"
            "sys.path.insert(0, 'src')\n"
            f"from {dotted_name} import *\n"
            f"print(repr({expression}))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        )
        return result.stdout + result.stderr

    def helper_names(self, location: str) -> T.List[str]:
        return self.names(self.function_node(location).helper_function_nodes)

    def all_function_nodes(self) -> T.List[T.Any]:
        """Returns the function nodes of env.module_node, including the method
        nodes and the helper function nodes."""

        def with_helpers(nodes):
            for node in nodes:
                yield node
                yield from with_helpers(node.helper_function_nodes)

        nodes = list(with_helpers(self.module_node.function_nodes))
        for class_node in self.module_node.class_nodes:
            nodes.extend(with_helpers(class_node.method_nodes))
        return nodes

    def top_level_function_names(self, module_name: str) -> T.List[str]:
        tree = ast.parse(self.read_module(module_name))
        return [
            statement.name
            for statement in tree.body
            if isinstance(statement, ast.FunctionDef)
        ]

    def called_names(self, module_name: str, function_name: str) -> T.Set[str]:
        """Returns the names of the functions that the top-level function
        calls directly by name."""
        tree = ast.parse(self.read_module(module_name))
        function_def = next(
            statement
            for statement in tree.body
            if isinstance(statement, ast.FunctionDef)
            and statement.name == function_name
        )
        return {
            node.func.id
            for node in ast.walk(function_def)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

    def function_source(self, module_name: str, function_name: str) -> str:
        source = self.read_module(module_name)
        tree = ast.parse(source)
        function_def = next(
            statement
            for statement in tree.body
            if isinstance(statement, ast.FunctionDef)
            and statement.name == function_name
        )
        return ast.get_source_segment(source, function_def)

    def glossary_names(self) -> T.Set[str]:
        """Returns the names and the aliases of the entries of env.glossary."""
        return {
            name
            for entry in self.glossary.entries
            for name in [entry.name, *entry.aliases]
        }
