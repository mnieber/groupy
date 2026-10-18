import json
import os
import shlex
import sys
import typing as T
from pathlib import Path

import yaml
from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.models.rfr import Rfr
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.claude_requests.rules.create_rfr_policy import create_rfr_policy
from groupy.sessions.rules.load_config import load_config

__all__ = ["Context", "TestEnv"]

FAKE_CLAUDE_PY = Path(__file__).parent / "fake_claude.py"


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the Claude policies, where a fake claude executable on
    the PATH runs the scripted steps of each request."""

    def __init__(self, context: Context):
        self.fake_dir = context.repo_dir.parent / "fake-claude"
        super().__init__(context)

    # Actions

    def create_session_with_claude_policies(self) -> None:
        """Creates a session for the myapp package, with a config that uses
        the real Claude policies and the model haiku, and puts the fake claude
        executable on the PATH."""
        self.create_repo_with_target_code()
        config_lines = [
            "grouping_strategy: simple",
            "max_group_lines: 10000",
            "max_chunk_lines: 10000",
            "claude_model: haiku",
        ]
        self.write_file(".groupy/config.yaml", "\n".join(config_lines) + "\n")
        self.commit_all("add groupy config")
        self.run_groupy("init", "--target-dir=src")

        # The fake claude runs groupy with the Python of the tests
        bin_dir = self.fake_dir / "bin"
        bin_dir.mkdir(parents=True)
        claude_path = bin_dir / "claude"
        claude_path.write_text(f"#!{sys.executable}\n" + FAKE_CLAUDE_PY.read_text())
        claude_path.chmod(0o755)
        path = os.pathsep.join(
            [str(bin_dir), str(Path(sys.executable).parent), os.environ["PATH"]]
        )
        self.context.monkeypatch.setenv("PATH", path)
        self.context.monkeypatch.setenv("FAKE_CLAUDE_DIR", str(self.fake_dir))

    def script_claude(
        self,
        request_id: str,
        *steps: T.Dict[str, str],
        exit_code: int = 0,
        stderr: str = "",
    ) -> None:
        """Scripts what the fake claude does for the request: the steps (see
        run_callback and write_file) and its exit code and stderr."""
        scripts_dir = self.fake_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        script = {"steps": list(steps), "exit_code": exit_code, "stderr": stderr}
        (scripts_dir / _file_name(request_id)).write_text(json.dumps(script))

    def run_rfa(self, rfa_id: str, context: T.Dict[str, T.Any] = None) -> None:
        """Runs the RFA with the RFA policy of the config."""
        rfa_policy = create_rfa_policy(load_config(Path(".groupy/config.yaml")))
        rfa_policy.run(Rfa(id=rfa_id, prompt="Analyze the code", context=context or {}))

    def run_rfr(self, rfr_id: str, context: T.Dict[str, T.Any] = None) -> None:
        """Runs the RFR with the RFR policy of the config."""
        rfr_policy = create_rfr_policy(load_config(Path(".groupy/config.yaml")))
        rfr_policy.run(
            Rfr(id=rfr_id, prompt="Refactor the code", context=context or {})
        )

    # Queries (for use in asserts)

    def claude_record(self, request_id: str) -> T.Dict[str, T.Any]:
        """Returns what the fake claude recorded for the request: its argv,
        the GROUPY_* env vars and the outputs of the commands."""
        record_path = self.fake_dir / "records" / _file_name(request_id)
        return json.loads(record_path.read_text())

    def claude_prompt(self, request_id: str) -> str:
        argv = self.claude_record(request_id)["argv"]
        return argv[argv.index("-p") + 1]

    def claude_option(self, request_id: str, option: str) -> T.List[str]:
        """Returns the values that follow the option in the argv of claude."""
        argv = self.claude_record(request_id)["argv"]
        values = []
        for arg in argv[argv.index(option) + 1 :]:
            if arg.startswith("--"):
                break
            values.append(arg)
        return values

    def command_outputs(self, request_id: str) -> T.List[str]:
        """Returns the outputs of the commands that the fake claude ran."""
        return [
            output["output"] for output in self.claude_record(request_id)["outputs"]
        ]

    def request_context(self, request_id: str) -> T.Dict[str, T.Any]:
        """Returns the context file of the request, as plain data."""
        return yaml.safe_load(self.request_file(request_id, "context.yaml"))

    def request_file(self, request_id: str, file_name: str) -> str:
        return self.read_file(f".groupy/requests/{request_id}/{file_name}")

    def request_file_exists(self, request_id: str, file_name: str) -> bool:
        return self.file_exists(f".groupy/requests/{request_id}/{file_name}")


def run_callback(name: str, /, **args: T.Any) -> T.Dict[str, str]:
    """Returns a step for a script of the fake claude, that runs the callback
    with groupy callback, as Claude would."""
    return {"run": f"groupy callback {name} --args {shlex.quote(json.dumps(args))}"}


def write_file(file_path: str, text: str) -> T.Dict[str, str]:
    """Returns a step for a script of the fake claude, that writes the text to
    the file (relative to the repo dir), as Claude would in an RFR."""
    return {"write_file": file_path, "text": text}


def _file_name(request_id: str) -> str:
    return request_id.replace("/", "__") + ".json"
