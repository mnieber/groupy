import argparse
import json
import logging
import os
import sys
import traceback

from groupy import settings
from groupy.claude_requests.actions.run_requested_callback import (
    RequestStoppedError,
    run_requested_callback,
)
from groupy.claude_requests.models.callback import Callback
from groupy.claude_requests.rules.get_claude_costs import get_claude_costs
from groupy.claude_requests.rules.get_current_request_dir import (
    get_current_request_dir,
)
from groupy.claude_requests.rules.get_retry_instruction import get_retry_instruction
from groupy.claude_requests.rules.get_stop_instruction import get_stop_instruction
from groupy.claude_requests.rules.is_request_stopped import is_request_stopped
from groupy.claude_requests.utils.to_plain_data import to_plain_data
from groupy.nodes.actions.sync_node_files import sync_node_files
from groupy.runtime.actions.run_next_stage import run_next_stage
from groupy.sessions.actions.init_session import init_session
from groupy.sessions.actions.reset_to_tag import reset_to_tag
from groupy.sessions.enums import RunResults, Stages
from groupy.sessions.models.session import get_session
from groupy.sessions.rules.get_developer_commits import get_developer_commits
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_remaining_request_ids import get_remaining_request_ids
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.get_stage_commit_count import get_stage_commit_count
from groupy.sessions.rules.get_stage_guide import get_stage_guide
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.sessions.rules.load_config import load_config
from groupy.sessions.rules.load_last_run import load_last_run
from groupy.sessions.utils.exceptions import (
    DirtyWorkingTreeError,
    NoGroupFileError,
    NoSessionError,
)
from groupy.utils.dump_yaml import dump_yaml
from groupy.utils.format_error import format_error
from groupy.utils.has_git_tag import has_git_tag
from groupy.utils.run_git import run_git

logger = logging.getLogger(__name__)

RISKS_TEXT = """\
Groupy radically refactors the code in {target_dir}, using rope and Claude. This
may introduce errors in the code.

- You remain fully responsible for the correctness of the code. Review all changes
  carefully: Groupy commits each change on the branch {branch}, so that you can
  review (and undo) them with git.
- Groupy runs Claude Code for its requests to Claude, which incurs costs (on your
  AI model provider account, or within the limits of your subscription). You are
  responsible for these costs. groupy status shows an estimate of the costs so
  far, based on what Claude Code reports. This estimate comes without any
  guarantee: it may be incomplete or wrong, so check your actual usage and costs
  with your AI model provider.

Groupy is provided as is, without warranty of any kind. See also: LICENSE.
"""

ERROR_HINTS = {
    DirtyWorkingTreeError: "Commit or stash your changes, or run groupy reset to "
    "undo the current stage.",
    NoGroupFileError: "Restore the group file .groupy/groups.txt (e.g. from git).",
    NoSessionError: "Run groupy init to start a session.",
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Groupy - a tool that takes a Python code-base apart and rebuilds it"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Init command
    init_parser = subparsers.add_parser("init", help="Start a groupy session")
    init_parser.add_argument(
        "--target-dir", required=True, help="The dir with the target code"
    )
    init_parser.add_argument(
        "--branch-name", default="groupy", help="The branch to create"
    )
    init_parser.add_argument(
        "--accept-risks",
        action="store_true",
        help="Accept the risks of using groupy without being asked",
    )

    # Next command
    subparsers.add_parser("next", help="Run the next stage of the session")

    # Sync command
    subparsers.add_parser(
        "sync", help="Update the node files after the source was changed by hand"
    )

    # Status command
    subparsers.add_parser("status", help="Show the state of the session")

    # Reset command
    reset_parser = subparsers.add_parser(
        "reset", help="Reset the session to the start of the current stage"
    )
    reset_parser.add_argument(
        "--init", action="store_true", help="Reset to the start of the session"
    )
    reset_parser.add_argument(
        "--yes", action="store_true", help="Don't ask for confirmation"
    )

    # Callback command
    callback_parser = subparsers.add_parser(
        "callback", help="Run a callback of Groupy (used by Claude)"
    )
    callback_parser.add_argument("name", help="The name of the callback")
    callback_parser.add_argument(
        "--args", default="{}", help="The arguments, as a JSON object"
    )

    # Global arguments
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )

    return parser.parse_args(argv)


def _setup_logging(verbosity):
    log_level = logging.WARNING
    if verbosity >= 2:
        log_level = logging.DEBUG
    elif verbosity >= 1:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")


def _init(args):
    if not args.accept_risks:
        print(RISKS_TEXT.format(target_dir=args.target_dir, branch=args.branch_name))
        try:
            answer = input("Do you accept these risks? [y/N] ")
        except EOFError:
            answer = ""
        if answer.strip().lower() not in ("y", "yes"):
            print(
                "groupy init was cancelled, nothing was changed. "
                "(Use --accept-risks to accept the risks without being asked.)"
            )
            return 1
    init_session(args.target_dir, args.branch_name)
    return 0


def _sync():
    lines = sync_node_files(get_source_root(), get_groupy_path("groups.txt"))
    if not lines:
        print("The node files match the source.")
        return
    for line in lines:
        print(line)
    print(
        "Please review the changes to the node files (e.g. with git diff), "
        "and move the analysis of renamed nodes."
    )


def _print_stage_report(stage):
    guide = get_stage_guide(stage)
    print(
        f"The stage {stage.value} finished "
        f"({get_stage_commit_count(stage)} commits)."
    )
    print(f"Please review {guide.review}.")
    print("You may edit the node files, and commit your edits, before you continue.")
    _print_next_stage(Stages(get_session().next_stage), "start")


def _print_next_stage(stage, verb):
    if stage == Stages.DONE:
        print("The refactoring is done.")
        return
    description = get_stage_guide(stage).description
    print(f"groupy next will {verb} {stage.value}, which {description}.")


def _status():
    session = get_session()
    print(f"Target dir: {session.target_dir}")

    # The last run
    last_run = load_last_run()
    if last_run is None:
        print("groupy next has not run yet.")
    else:
        location = last_run.request_id or last_run.stage
        if last_run.result == RunResults.FINISHED.value:
            print(f"The last groupy next finished {last_run.stage}.")
            review = get_stage_guide(Stages(last_run.stage)).review
            print(f"Please review {review}.")
        elif last_run.result == RunResults.INTERRUPTED.value:
            print(
                f"The last groupy next was interrupted in {location}: "
                f"{last_run.error}"
            )
        else:
            print(
                f"The last groupy next was aborted in {location} "
                "(the process crashed or was killed)."
            )

    # The next stage
    stage = Stages(session.next_stage)
    if stage != Stages.DONE and has_git_tag(get_start_tag(stage)):
        _print_next_stage(stage, "resume")
        config = load_config(get_groupy_path("config.yaml"))
        remaining = get_remaining_request_ids(session, config)
        print(f"Finished chunks: {', '.join(session.finished_chunks) or 'none'}")
        print(f"Remaining chunks: {', '.join(remaining) or 'none'}")
    else:
        _print_next_stage(stage, "start")

    # The costs of Claude, which are a lower bound when the cost of a session is
    # unknown
    costs = get_claude_costs()
    prefix = "" if costs.is_complete else "at least "
    print(f"Claude costs so far: {prefix}{costs.total_usd:.2f} USD")

    # The working tree
    if run_git("status", "--porcelain"):
        print(
            "The working tree is not clean: commit or stash your changes, or run "
            "groupy reset to undo the current stage."
        )
    else:
        print("The working tree is clean.")


def _reset(args):
    session = get_session()
    stage = None if args.init else Stages(session.next_stage)
    tag = get_start_tag(stage)
    if not has_git_tag(tag):
        print(f"There is nothing to reset: {session.next_stage} has not started.")
        return
    target = (
        "the start of the session" if stage is None else f"the start of {stage.value}"
    )

    # List what will be lost
    print(f"groupy reset will reset the repo to {target}.")
    commits = get_developer_commits(tag)
    if commits:
        print("These commits (that groupy didn't make) will be lost:")
        for commit in commits:
            print(f"  {commit}")
    changes = run_git("status", "--porcelain").splitlines()
    if changes:
        print("These uncommitted changes will be lost:")
        for change in changes:
            print(f"  {change}")

    if not args.yes:
        answer = input("Do you want to continue? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Nothing was reset.")
            return

    previous_head = reset_to_tag(tag)
    print(f"The repo was reset to {target}.")
    print(f"To undo the reset, run: git reset --hard {previous_head}")


def _callback(args):
    # Claude may have changed its cwd
    if settings.GROUPY_REPO_DIR:
        os.chdir(settings.GROUPY_REPO_DIR)
    try:
        result = run_requested_callback(Callback(args.name, json.loads(args.args)))
    except Exception as error:
        if not isinstance(error, RequestStoppedError):
            print(f"The callback failed: {format_error(error)}")
        request_dir = get_current_request_dir()
        if request_dir is not None and is_request_stopped(request_dir):
            print(get_stop_instruction())
        elif request_dir is not None:
            print(get_retry_instruction())
        return 1
    if result is None:
        print("OK")
    elif isinstance(result, str):
        print(result.rstrip("\n"))
    else:
        print(dump_yaml(to_plain_data(result)), end="")
    return 0


def _print_error(error, verbose):
    stage_id = getattr(error, "groupy_stage_id", None)
    if stage_id:
        request_id = getattr(error, "groupy_request_id", "") or stage_id
        lines = [
            f"The stage {stage_id} was interrupted in {request_id}.",
            format_error(error),
            "Groupy restored the working tree to the last commit. The committed "
            "changes are kept (see git log), and the finished chunks will be "
            "skipped.",
            "Repair the cause (e.g. edit the code or a node file), commit the "
            "repair, and run groupy next to resume the stage (or groupy reset to "
            "redo it).",
        ]
    else:
        lines = [format_error(error)]
        if type(error) in ERROR_HINTS:
            lines.append(ERROR_HINTS[type(error)])
    if verbose:
        lines.append(
            "".join(traceback.format_exception(type(error), error, error.__traceback__))
        )
    for line in lines:
        print(line, file=sys.stderr)


def _run_command(args):
    if args.command == "init":
        return _init(args)
    elif args.command == "next":
        run_next_stage()
    elif args.command == "sync":
        _sync()
    elif args.command == "status":
        _status()
    elif args.command == "reset":
        _reset(args)
    elif args.command == "callback":
        return _callback(args)
    else:
        print("Please specify a command. Use --help for more information.")
        return 1

    return 0


def main(argv=None):
    args = _parse_args(argv)
    _setup_logging(args.verbose)
    return _run_command(args)


def run(argv=None):
    # Runs groupy for the developer: errors are printed instead of raised, and
    # groupy next reports what to review
    args = _parse_args(argv)
    _setup_logging(args.verbose)
    try:
        if args.command == "next":
            stage = run_next_stage()
            if stage is not None:
                _print_stage_report(stage)
            return 0
        return _run_command(args)
    except KeyboardInterrupt as error:
        _print_error(error, args.verbose)
        return 130
    except Exception as error:
        _print_error(error, args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(run())
