import re
import typing as T
from pathlib import Path

import yaml
from groupy_next_tests.fake_policies import (
    FakeRefactoringPolicy,
    FakeRfaPolicy,
    FakeRfrPolicy,
    FileWrite,
    get_fake_refactoring_policy,
    get_fake_rfa_policy,
    get_fake_rfr_policy,
    reset_fake_policies,
)
from sessions_tests.groupy_test_env import Context
from sessions_tests.groupy_test_env import TestEnv as GroupyTestEnv

from groupy.call_graph.models.call_graph_view import FunctionView
from groupy.claude_requests.actions.run_callback import NODE_EDITS
from groupy.claude_requests.models.callback import Callback
from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.models.rfr import Rfr
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.functions.actions.add_responsibility import add_responsibility
from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.rules.load_module_node import load_module_node
from groupy.runtime.actions.run_next_stage import STAGE_ACTIONS
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.enums import Stages
from groupy.sessions.models.session import get_session
from groupy.sessions.rules.load_config import load_config

__all__ = ["Context", "TestEnv"]

FAKE_RFA_POLICY = "groupy_next_tests.fake_policies:get_fake_rfa_policy"

FAKE_RFR_POLICY = "groupy_next_tests.fake_policies:get_fake_rfr_policy"

FAKE_REFACTORING_POLICY = "groupy_next_tests.fake_policies:get_fake_refactoring_policy"

# The fake stage replaces the first real stage, so that the tests of the stage
# runner don't depend on what the real stages do.
FAKE_STAGE = Stages.IDENTIFY_HELPER_FUNCTIONS


def run_fake_stage() -> None:
    """Makes an RFA per chunk, like most stages do."""
    config = load_config(Path(".groupy") / "config.yaml")
    rfa_policy = create_rfa_policy(config)
    source_root = Path(get_session().target_dir)

    def run_chunk(chunk: Chunk, rfa_id: str) -> None:
        rfa_policy.run(
            Rfa(
                id=rfa_id,
                prompt="Analyze the modules of the chunk",
                context={"module_names": chunk.module_names},
            )
        )

    chunks = get_chunks(
        source_root, Path(".groupy") / "groups.txt", config.max_chunk_lines
    )
    process_chunks(FAKE_STAGE, chunks, run_chunk)


class TestEnv(GroupyTestEnv):
    def __init__(self, context: Context):
        # The fake policy is a singleton, so the script of an earlier test must
        # not leak into this one.
        reset_fake_policies()
        self.source_root = context.repo_dir / "src"
        self.module_node: ModuleNode = None
        self.output_lines: T.List[str] = []
        self.error_lines: T.List[str] = []
        super().__init__(context)

    # Actions

    def create_session(
        self, modules: T.Dict[str, str] = None, **config_fields: T.Any
    ) -> None:
        """Creates a git repo with the target code and a config file that uses
        the fake RFA, RFR and refactoring policies, and runs groupy init and
        the first stage (group-modules). The
        modules (a map from module name to text) are added to the target code,
        and the config_fields are added to the config file."""
        self.create_repo_with_target_code()
        for module_name, text in (modules or {}).items():
            self.write_file(f"src/{module_name}", text)
        config_lines = [
            f"rfa_policy: {FAKE_RFA_POLICY}",
            f"rfr_policy: {FAKE_RFR_POLICY}",
            f"refactoring_policy: {FAKE_REFACTORING_POLICY}",
        ] + [f"{field}: {value}" for field, value in config_fields.items()]
        self.write_file(".groupy/config.yaml", "\n".join(config_lines) + "\n")
        self.commit_all("add groupy config")
        self.run_groupy("init", "--accept-risks", "--target-dir=src")
        # The first stage (group-modules) creates the group file
        self.run_groupy("next")

    def run_groupy_next(self) -> None:
        """Runs groupy next and stores the lines that it prints in
        env.output_lines, and the lines that it prints on stderr (e.g. the
        progress messages) in env.error_lines (this needs context.capsys)."""
        self.context.capsys.readouterr()
        try:
            self.run_groupy("next")
        finally:
            captured = self.context.capsys.readouterr()
            self.output_lines = captured.out.splitlines()
            self.error_lines = captured.err.splitlines()

    def run_groupy_next_and_catch_error(self) -> None:
        """Runs run_groupy_next, and stores the exception it is expected to
        raise in env.error."""
        try:
            self.run_groupy_next()
        except Exception as error:
            self.error = error

    def install_fake_stage(self) -> None:
        self.context.monkeypatch.setitem(STAGE_ACTIONS, FAKE_STAGE, run_fake_stage)

    def script_rfa(self, rfa_id: str, *callbacks: Callback) -> None:
        self.rfa_policy().scripts[rfa_id] = list(callbacks)

    def clear_rfa_requests(self) -> None:
        self.rfa_policy().requests.clear()

    def script_rfr(self, rfr_id: str, *steps: T.Union[FileWrite, Callback]) -> None:
        self.rfr_policy().scripts[rfr_id] = list(steps)

    def fail_refactoring(self, module_name: str, name: str) -> None:
        """Lets the fake refactoring policy raise an error when it refactors
        the symbol name (or @module, for move_module) in the module."""
        self.refactoring_policy().failing_refactorings.add((module_name, name))

    def clear_failing_refactorings(self) -> None:
        self.refactoring_policy().failing_refactorings.clear()

    def clear_refactoring_calls(self) -> None:
        self.refactoring_policy().calls.clear()

    def edit_node_file(
        self, action: T.Callable, module_name: str, location: str, *args
    ) -> None:
        """Runs the node file edit (e.g. set_renaming) on the node at the
        location, as the earlier stages or the developer would."""
        action(self.source_root, module_name, location, *args)

    def load_module_node(self, module_name: str) -> None:
        """Loads the node file of the module into env.module_node."""
        self.module_node = load_module_node(
            self.source_root / f"{module_name}.groupy.yaml"
        )

    def press_ctrl_c_in_add_responsibility(self) -> None:
        """Lets the add_responsibility callback raise a KeyboardInterrupt
        (as if the developer pressed Ctrl+C) after it has changed the node
        file, but before Groupy commits the change."""

        def add_responsibility_and_press_ctrl_c(source_root, **args):
            add_responsibility(source_root, **args)
            raise KeyboardInterrupt()

        self.context.monkeypatch.setitem(
            NODE_EDITS, "add_responsibility", add_responsibility_and_press_ctrl_c
        )

    def tag_head(self, tag: str) -> None:
        self.run_git("tag", tag)

    def set_next_stage(self, stage_id: str) -> None:
        """Sets next_stage in the session file, and commits it (as if the
        earlier stages have run)."""
        session_path = ".groupy/session.yaml"
        text = self.read_file(session_path)
        self.write_file(
            session_path,
            re.sub(r"^next_stage: .*$", f"next_stage: {stage_id}", text, flags=re.M),
        )
        self.commit_all(f"start at {stage_id}")

    def set_session_exclude(self, *patterns: str) -> None:
        """Lets the developer replace the exclude patterns in the session file,
        and commits it."""
        session_path = ".groupy/session.yaml"
        data = yaml.safe_load(self.read_file(session_path))
        data["exclude"] = list(patterns)
        self.write_file(session_path, yaml.safe_dump(data))
        self.commit_all("set the exclude patterns")

    def catch_error(self, env_action: T.Callable, *args, **kwargs) -> None:
        """Runs the env action and stores the exception it is expected to
        raise in env.error."""
        self.error = None
        try:
            env_action(*args, **kwargs)
        except Exception as error:
            self.error = error

    # Queries (for use in asserts)

    def rfa_policy(self) -> FakeRfaPolicy:
        return get_fake_rfa_policy()

    def rfr_policy(self) -> FakeRfrPolicy:
        return get_fake_rfr_policy()

    def rfr_ids(self) -> T.List[str]:
        return [rfr.id for rfr in self.rfr_policy().requests]

    def refactoring_policy(self) -> FakeRefactoringPolicy:
        return get_fake_refactoring_policy()

    def refactoring_calls(self, method: str) -> T.List[T.Tuple[str, str]]:
        """Returns the (module_name, name) pairs of the calls of the method
        (e.g. move_symbol) of the fake refactoring policy, in the order in
        which they were made."""
        return [
            (module_name, name)
            for called_method, module_name, name in self.refactoring_policy().calls
            if called_method == method
        ]

    def renamed_names(self) -> T.List[T.Tuple[str, str]]:
        return self.refactoring_calls("rename_symbol")

    def rfa_ids(self) -> T.List[str]:
        return [rfa.id for rfa in self.rfa_policy().requests]

    def rfa(self, rfa_id: str) -> Rfa:
        matches = [rfa for rfa in self.rfa_policy().requests if rfa.id == rfa_id]
        assert len(matches) == 1, f"Expected one RFA with the id {rfa_id}"
        return matches[0]

    def rfr(self, rfr_id: str) -> Rfr:
        matches = [rfr for rfr in self.rfr_policy().requests if rfr.id == rfr_id]
        assert len(matches) == 1, f"Expected one RFR with the id {rfr_id}"
        return matches[0]

    def function_view_in_context(self, rfa_id: str, location: str) -> FunctionView:
        """Returns the function view at the location, in the call graph view
        in the context of the RFA."""
        view = self.rfa(rfa_id).context["call_graph_view"]
        matches = [v for v in view.function_views if v.location == location]
        assert len(matches) == 1, f"Expected one function view for {location}"
        return matches[0]

    def read_module(self, module_name: str) -> str:
        return (self.source_root / module_name).read_text()

    def names(self, nodes: T.List[T.Any]) -> T.List[str]:
        return [node.name for node in nodes]

    def function_node(self, location: str):
        """Returns the function node at the location in env.module_node, where
        the location is the qualified name of the node in the node file (e.g.
        `create_book`, `Book.save`, or `create_report._format_lines` for a
        helper function node)."""
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

    def class_node(self, name: str):
        return _find_by_name(self.module_node.class_nodes, name)

    def variable_node(self, name: str):
        return _find_by_name(self.module_node.variable_nodes, name)

    def commit_messages_since_remembered_head(self) -> T.List[str]:
        log = self._git(
            "log", "--reverse", "--format=%s", f"{self.remembered_git_head}..HEAD"
        )
        return log.splitlines()

    def responsibilities(self, module_name: str, function_name: str) -> T.List[str]:
        module_node = load_module_node(self.source_root / f"{module_name}.groupy.yaml")
        matches = [
            node for node in module_node.function_nodes if node.name == function_name
        ]
        assert len(matches) == 1, f"Expected one function node for {function_name}"
        return matches[0].responsibilities


def callback(name: str, /, **args: T.Any) -> Callback:
    """Returns a callback for a script. The args are the arguments of the
    action, without the source root and the glossary path, which the callback
    dispatcher supplies."""
    return Callback(name=name, args=args)


def file_write(module_name: str, text: str) -> FileWrite:
    """Returns a step for an RFR script that writes the new text of the
    module, where the module name is relative to the target dir (src)."""
    return FileWrite(file_path=f"src/{module_name}", text=text)


def _find_by_name(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]
