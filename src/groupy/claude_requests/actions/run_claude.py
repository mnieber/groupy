import os
import shutil
import subprocess
import time
import typing as T

from groupy.claude_requests.rules.get_preamble import get_preamble
from groupy.claude_requests.rules.get_request_dir import get_request_dir
from groupy.claude_requests.rules.load_callback_error import load_callback_error
from groupy.claude_requests.utils.to_plain_data import to_plain_data
from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.utils.dump_yaml import dump_yaml

# How long Claude may continue after a failed callback, before it is stopped
STOP_TIMEOUT_SECONDS = 300

RFA_TOOLS = ["Read", "Glob", "Grep", "Bash"]

RFR_TOOLS = [*RFA_TOOLS, "Edit", "Write"]


def run_claude(
    request_id: str,
    prompt: str,
    context: T.Dict[str, T.Any],
    claude_model: str,
    in_rfr: bool,
) -> None:
    # Write the context of the request
    request_dir = get_request_dir(request_id)
    shutil.rmtree(request_dir, ignore_errors=True)
    request_dir.mkdir(parents=True)
    context_path = request_dir / "context.yaml"
    context_path.write_text(dump_yaml(to_plain_data(context)))

    # Run Claude in headless mode, where it can only use the given tools, and only
    # run groupy callbacks with Bash
    tools = RFR_TOOLS if in_rfr else RFA_TOOLS
    allowed_tools = [
        "Bash(groupy callback:*)" if tool == "Bash" else tool for tool in tools
    ]
    command = [
        "claude",
        "-p",
        prompt
        + "\n"
        + get_preamble(request_id, context_path, get_source_root(), in_rfr),
        "--output-format",
        "stream-json",
        "--verbose",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--permission-mode",
        "dontAsk",
        "--tools",
        ",".join(tools),
        "--allowedTools",
        *allowed_tools,
    ]
    if claude_model:
        command += ["--model", claude_model]
    env = {
        **os.environ,
        "GROUPY_REPO_DIR": os.getcwd(),
        "GROUPY_REQUEST_DIR": str(request_dir.resolve()),
        "GROUPY_IN_RFR": "1" if in_rfr else "",
    }

    # The log of the session is kept for debugging, and for the costs. A request
    # that runs again adds a session to its log.
    log_path = get_branch_dir() / "logs" / f"{request_id}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path = request_dir / "stderr.txt"
    with log_path.open("a") as log_file, stderr_path.open("w") as stderr_file:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=stderr_file,
            env=env,
        )
        try:
            _wait_for_claude(process, request_dir)
        except BaseException:
            # E.g. Ctrl+C: Claude may have edited files in an RFR
            process.terminate()
            process.wait()
            restore_working_tree()
            raise

    # A callback that failed twice in a row ends the request with its error
    error = load_callback_error(request_dir)
    if error is not None:
        restore_working_tree()
        raise error
    if process.returncode != 0:
        stderr_tail = stderr_path.read_text()[-2000:]
        raise ClaudeRequestError(
            f"Claude failed in the request {request_id} (exit code "
            f"{process.returncode}): {stderr_tail}"
        )


def _wait_for_claude(process: subprocess.Popen, request_dir) -> None:
    # Claude is asked to stop after a failed callback, and stopped when it
    # continues for too long
    error_time = None
    while process.poll() is None:
        if error_time is None and (request_dir / "error.yaml").exists():
            error_time = time.monotonic()
        if error_time and time.monotonic() - error_time > STOP_TIMEOUT_SECONDS:
            process.terminate()
            process.wait()
            return
        time.sleep(0.5)


class ClaudeRequestError(Exception):
    pass
