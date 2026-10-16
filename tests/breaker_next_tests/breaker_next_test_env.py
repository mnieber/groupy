import re
import typing as T
from pathlib import Path

from breaker.call_graph.models.call_graph_view import FunctionView
from breaker.claude_requests.models.callback import Callback
from breaker.claude_requests.models.rfa import Rfa
from breaker.claude_requests.rules.create_rfa_policy import create_rfa_policy
from breaker.groups.models.chunk import Chunk
from breaker.groups.rules.get_chunks import get_chunks
from breaker.nodes.rules.load_module_node import load_module_node
from breaker.runtime.actions.run_next_stage import STAGE_ACTIONS
from breaker.sessions.actions.process_chunks import process_chunks
from breaker.sessions.enums import Stages
from breaker.sessions.models.session import get_session
from breaker.sessions.rules.load_config import load_config
from breaker_next_tests.fake_policies import (
    FakeRfaPolicy,
    get_fake_rfa_policy,
    reset_fake_policies,
)
from sessions_tests.breaker_test_env import Context
from sessions_tests.breaker_test_env import TestEnv as BreakerTestEnv

__all__ = ["Context", "TestEnv"]

FAKE_RFA_POLICY = "breaker_next_tests.fake_policies:get_fake_rfa_policy"

# The fake stage replaces the first real stage, so that the tests of the stage
# runner don't depend on what the real stages do.
FAKE_STAGE = Stages.IDENTIFY_HELPER_FUNCTIONS


def run_fake_stage() -> None:
    """Makes an RFA per chunk, like most stages do."""
    config = load_config(Path(".breaker") / "config.yaml")
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
        source_root, Path(".breaker") / "groups.txt", config.max_chunk_lines
    )
    process_chunks(FAKE_STAGE, chunks, run_chunk)


class TestEnv(BreakerTestEnv):
    def __init__(self, context: Context):
        # The fake policy is a singleton, so the script of an earlier test must
        # not leak into this one.
        reset_fake_policies()
        super().__init__(context)

    # Actions

    def create_session(
        self, modules: T.Dict[str, str] = None, **config_fields: T.Any
    ) -> None:
        """Creates a git repo with the target code and a config file that uses
        the fake RFA policy, and runs breaker init. The modules (a map from
        module name to text) are added to the target code, and the
        config_fields are added to the config file."""
        self.create_repo_with_target_code()
        for module_name, text in (modules or {}).items():
            self.write_file(f"src/{module_name}", text)
        config_lines = [f"rfa_policy: {FAKE_RFA_POLICY}"] + [
            f"{field}: {value}" for field, value in config_fields.items()
        ]
        self.write_file(".breaker/config.yaml", "\n".join(config_lines) + "\n")
        self.commit_all("add breaker config")
        self.run_breaker("init", "--target-dir=src")

    def install_fake_stage(self) -> None:
        self.context.monkeypatch.setitem(STAGE_ACTIONS, FAKE_STAGE, run_fake_stage)

    def script_rfa(self, rfa_id: str, *callbacks: Callback) -> None:
        self.rfa_policy().scripts[rfa_id] = list(callbacks)

    def clear_rfa_requests(self) -> None:
        self.rfa_policy().requests.clear()

    def set_next_stage(self, stage_id: str) -> None:
        """Sets next_stage in the session file, and commits it (as if the
        earlier stages have run)."""
        session_path = ".breaker/session.yaml"
        text = self.read_file(session_path)
        self.write_file(
            session_path,
            re.sub(r"^next_stage: .*$", f"next_stage: {stage_id}", text, flags=re.M),
        )
        self.commit_all(f"start at {stage_id}")

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

    def rfa_ids(self) -> T.List[str]:
        return [rfa.id for rfa in self.rfa_policy().requests]

    def rfa(self, rfa_id: str) -> Rfa:
        matches = [rfa for rfa in self.rfa_policy().requests if rfa.id == rfa_id]
        assert len(matches) == 1, f"Expected one RFA with the id {rfa_id}"
        return matches[0]

    def function_view_in_context(self, rfa_id: str, location: str) -> FunctionView:
        """Returns the function view at the location, in the call graph view
        in the context of the RFA."""
        view = self.rfa(rfa_id).context["call_graph_view"]
        matches = [v for v in view.function_views if v.location == location]
        assert len(matches) == 1, f"Expected one function view for {location}"
        return matches[0]

    def commit_messages_since_remembered_head(self) -> T.List[str]:
        log = self._git(
            "log", "--reverse", "--format=%s", f"{self.remembered_git_head}..HEAD"
        )
        return log.splitlines()

    def responsibilities(self, module_name: str, function_name: str) -> T.List[str]:
        node_file_path = self.repo_dir / "src" / f"{module_name}.breaker.yaml"
        module_node = load_module_node(node_file_path)
        matches = [
            node for node in module_node.function_nodes if node.name == function_name
        ]
        assert len(matches) == 1, f"Expected one function node for {function_name}"
        return matches[0].responsibilities


def callback(name: str, **args: T.Any) -> Callback:
    """Returns a callback for a script. The args are the arguments of the
    action, without the source root and the glossary path, which the callback
    dispatcher supplies."""
    return Callback(name=name, args=args)
