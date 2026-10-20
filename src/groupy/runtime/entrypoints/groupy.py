import argparse
import json
import logging
import os
import re
import sys
import traceback

from groupy import settings
from groupy.claude_requests.actions.run_requested_callback import (
    RequestStoppedError,
    run_requested_callback,
)
from groupy.claude_requests.models.callback import Callback
from groupy.claude_requests.rules.get_claude_costs import get_claude_costs
from groupy.claude_requests.rules.get_current_request_dir import get_current_request_dir
from groupy.claude_requests.rules.get_retry_instruction import get_retry_instruction
from groupy.claude_requests.rules.get_stop_instruction import get_stop_instruction
from groupy.claude_requests.rules.is_request_stopped import is_request_stopped
from groupy.claude_requests.utils.to_plain_data import to_plain_data
from groupy.nodes.actions.sync_node_files import sync_node_files
from groupy.runtime.actions.run_next_stage import run_next_stage
from groupy.sessions.actions.abort_branch import abort_branch
from groupy.sessions.actions.discard_and_checkout import discard_and_checkout
from groupy.sessions.actions.init_session import (
    BranchExistsError,
    InitSessionForm,
    NoBaseBranchError,
    init_session,
)
from groupy.sessions.actions.reset_to_tag import reset_to_tag
from groupy.sessions.enums import RunResults, Stages
from groupy.sessions.models.session import get_session
from groupy.sessions.rules.get_aborted_branches import get_aborted_branches
from groupy.sessions.rules.get_current_branch import get_current_branch
from groupy.sessions.rules.get_groupy_branch_session import get_groupy_branch_session
from groupy.sessions.rules.get_groupy_branches import get_groupy_branches
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_lost_commit_count import get_lost_commit_count
from groupy.sessions.rules.get_new_branch_name import get_new_branch_name
from groupy.sessions.rules.get_remaining_request_ids import get_remaining_request_ids
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.get_stage_commit_count import get_stage_commit_count
from groupy.sessions.rules.get_stage_guide import get_stage_guide
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.sessions.rules.get_started_stage_tag import get_started_stage_tag
from groupy.sessions.rules.get_uncommitted_changes import get_uncommitted_changes
from groupy.sessions.rules.load_config import load_config
from groupy.sessions.rules.load_last_run import load_last_run
from groupy.sessions.utils.exceptions import (
    DetachedHeadError,
    DirtyWorkingTreeError,
    NoGroupFileError,
    NoGroupyBranchError,
    NoSessionError,
    StageNotStartedError,
)
from groupy.utils.dump_yaml import dump_yaml
from groupy.utils.format_error import format_error
from groupy.utils.has_git_tag import has_git_tag
from groupy.utils.run_git import run_git
from groupy.utils.try_run_git import try_run_git

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
    BranchExistsError: "Choose another branch name with --branch-name, or leave it "
    "out to let groupy choose one.",
    DirtyWorkingTreeError: "Commit or stash your changes, or run groupy reset to "
    "undo the current stage.",
    NoBaseBranchError: "Use --base to choose the branch that the new branch starts "
    "from.",
    NoGroupFileError: "Restore the group file .groupy/groups.txt (e.g. from git).",
    DetachedHeadError: "Check out a groupy branch (e.g. with groupy switch "
    "<branch_name>).",
    NoGroupyBranchError: "Run groupy status --all to see the groupy branches.",
    NoSessionError: "Run groupy switch <branch_name> to continue a session, or "
    "groupy init to start one.",
    StageNotStartedError: "Choose a stage that has started (e.g. with groupy "
    "status --all).",
}

# How groupy status --all describes the result of the last run of a branch
LAST_RUN_TEXTS = {
    RunResults.FINISHED.value: "finished",
    RunResults.INTERRUPTED.value: "interrupted",
    # The process crashed or was killed
    RunResults.RUNNING.value: "aborted",
}

# The hints that differ per command, by command and error type
COMMAND_ERROR_HINTS = {
    ("init", DirtyWorkingTreeError): "Commit or stash your changes.",
}


# The stage names that the developer may give, where init is the start of the
# session
STAGE_NAMES = ["init", *[stage.value for stage in Stages if stage != Stages.DONE]]


def _stage_ref(value):
    # E.g. extract-methods or groupy-1/extract-methods
    branch_name, _, stage_name = value.rpartition("/")
    if stage_name not in STAGE_NAMES:
        raise argparse.ArgumentTypeError(f"{stage_name!r} is not a stage")
    return branch_name, stage_name


def _branch_name(value):
    # Keeps <branch_name>/<stage_name> unambiguous, and the per-branch dirs flat
    if "/" in value:
        raise argparse.ArgumentTypeError(f"{value!r} contains a /")
    return value


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Groupy - a tool that takes a Python code-base apart and rebuilds it"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Init command
    init_parser = subparsers.add_parser("init", help="Start a groupy session")
    init_parser.add_argument(
        "--target-dir",
        help="The dir with the target code (required without --from-stage)",
    )
    init_parser.add_argument(
        "--branch-name",
        type=_branch_name,
        help="The branch to create, without a / (default: groupy-<N>)",
    )
    init_parser.add_argument(
        "--base", default="main", help="The branch that the new branch starts from"
    )
    init_parser.add_argument(
        "--from-stage",
        type=_stage_ref,
        help="Start at the start of a stage ([<branch_name>/]<stage_name>)",
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
    status_parser = subparsers.add_parser(
        "status", help="Show the state of the session"
    )
    status_parser.add_argument(
        "--all", action="store_true", help="Show every groupy branch"
    )

    # Reset command
    reset_parser = subparsers.add_parser(
        "reset", help="Reset the current branch to the start of a stage"
    )
    reset_parser.add_argument(
        "stage",
        nargs="?",
        choices=STAGE_NAMES,
        help="The stage (default: the current stage), or init for the start of "
        "the session",
    )
    _add_force_argument(reset_parser)

    # Switch command
    switch_parser = subparsers.add_parser(
        "switch", help="Check out another groupy branch"
    )
    switch_parser.add_argument("branch_name", help="The groupy branch")
    _add_force_argument(switch_parser)

    # Leave command
    leave_parser = subparsers.add_parser(
        "leave", help="Go back to the base branch, and keep the groupy branch"
    )
    _add_force_argument(leave_parser)

    # Abort command
    abort_parser = subparsers.add_parser(
        "abort", help="Delete a groupy branch (by default the current one)"
    )
    abort_parser.add_argument("branch_name", nargs="?", help="The groupy branch")
    _add_force_argument(abort_parser)

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

    args = parser.parse_args(argv)
    if args.command == "init":
        if args.from_stage and args.target_dir:
            parser.error("argument --target-dir: not allowed with --from-stage")
        if not args.from_stage and not args.target_dir:
            parser.error("the following arguments are required: --target-dir")
    return args


def _add_force_argument(parser):
    parser.add_argument(
        "--force", action="store_true", help="Don't ask for confirmation"
    )


def _setup_logging(verbosity):
    log_level = logging.WARNING
    if verbosity >= 2:
        log_level = logging.DEBUG
    elif verbosity >= 1:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")


def _init(args):
    from_branch, from_stage = args.from_stage or ("", "")
    if not args.accept_risks:
        # With --from-stage, the target dir is in the session file
        target_dir = args.target_dir
        if from_stage:
            target_dir = get_groupy_branch_session(
                from_branch or get_current_branch()
            ).target_dir
        branch_name = args.branch_name or get_new_branch_name()
        print(RISKS_TEXT.format(target_dir=target_dir, branch=branch_name))
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
    init_session(
        InitSessionForm(
            target_dir=args.target_dir or "",
            branch_name=args.branch_name,
            base_branch=args.base,
            from_stage=from_stage,
            from_branch=from_branch,
        )
    )
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
    branch_name = get_current_branch()
    session = get_session()
    print(f"Branch: {branch_name}")
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

    # The costs of Claude on this branch
    costs = get_claude_costs()
    print(f"Claude costs so far: {_format_costs(costs.total_usd, costs.is_complete)}")

    # The working tree
    if run_git("status", "--porcelain"):
        print(
            "The working tree is not clean: commit or stash your changes, or run "
            "groupy reset to undo the current stage."
        )
    else:
        print("The working tree is clean.")


def _status_all():
    # Also works without a session, e.g. on the base branch
    current_branch = try_run_git("symbolic-ref", "--short", "-q", "HEAD")
    total_usd = 0.0
    is_complete = True
    lines = []
    branch_names = [
        *[(name, False) for name in get_groupy_branches()],
        *[(name, True) for name in get_aborted_branches()],
    ]
    for branch_name, is_aborted in sorted(branch_names, key=_natural_sort_key):
        costs = get_claude_costs(branch_name)
        total_usd += costs.total_usd
        is_complete = is_complete and costs.is_complete
        costs_text = f"costs {_format_costs(costs.total_usd, costs.is_complete)}"
        if is_aborted:
            lines.append(f"  {branch_name} (aborted): {costs_text}")
            continue
        marker = "*" if branch_name == current_branch else " "
        next_stage = get_groupy_branch_session(branch_name).next_stage
        last_run = load_last_run(branch_name)
        last_run_text = (
            "no run yet"
            if last_run is None
            else f"last run {LAST_RUN_TEXTS.get(last_run.result, last_run.result)}"
        )
        lines.append(
            f"{marker} {branch_name}: next stage {next_stage}, {last_run_text}, "
            f"{costs_text}"
        )
    for line in lines:
        print(line)
    print(f"Total costs: {_format_costs(total_usd, is_complete)}")


def _natural_sort_key(item):
    # E.g. groupy-2 comes before groupy-10
    return [
        int(part) if part.isdigit() else part for part in re.split(r"(\d+)", item[0])
    ]


def _format_costs(total_usd, is_complete):
    # The costs are a lower bound when the cost of a Claude session is unknown
    prefix = "" if is_complete else "at least "
    return f"{prefix}{total_usd:.2f} USD"


def _confirm_loss(command, changes, nr_of_commits=0, where="", force=False):
    # Returns whether the command may continue. When nothing will be lost, it
    # just continues.
    if not changes and not nr_of_commits:
        return True
    parts = []
    if nr_of_commits:
        parts.append(f"all {nr_of_commits} commits {where}")
    if changes:
        parts.append("these uncommitted changes:")
    print(f"groupy {command} will lose {' as well as '.join(parts)}")
    for change in changes:
        print(f"  {change}")
    if force:
        return True
    answer = input("Do you want to continue? [y/N] ")
    if answer.strip().lower() in ("y", "yes"):
        return True
    print("Nothing was changed.")
    return False


def _reset(args):
    session = get_session()
    stage_name = args.stage or session.next_stage
    stage = None if stage_name == "init" else Stages(stage_name)
    try:
        tag = get_started_stage_tag(stage)
    except StageNotStartedError:
        print(f"There is nothing to reset: {stage_name} has not started.")
        return
    target = (
        "the start of the session" if stage is None else f"the start of {stage.value}"
    )

    # Say what will be lost
    changes = get_uncommitted_changes()
    nr_of_commits = get_stage_commit_count(stage)
    if not changes and not nr_of_commits:
        print(f"The repo is already at {target}.")
        return
    if not _confirm_loss(
        "reset", changes, nr_of_commits, f"since {target}", force=args.force
    ):
        return

    previous_head = reset_to_tag(tag)
    print(f"The repo was reset to {target}.")
    print(f"To undo the reset, run: git reset --hard {previous_head}")


def _switch(args):
    session = get_groupy_branch_session(args.branch_name)
    if args.branch_name == try_run_git("symbolic-ref", "--short", "-q", "HEAD"):
        print(f"Already on {args.branch_name}.")
        return
    if not _confirm_loss("switch", get_uncommitted_changes(), force=args.force):
        return
    discard_and_checkout(args.branch_name)
    print(f"Switched to {args.branch_name} (next stage: {session.next_stage}).")


def _leave(args):
    branch_name = get_current_branch()
    session = get_session()
    if not _confirm_loss("leave", get_uncommitted_changes(), force=args.force):
        return
    discard_and_checkout(session.base_branch)
    print(f"Left {branch_name}; it is kept. Back on {session.base_branch}.")


def _abort(args):
    current_branch = try_run_git("symbolic-ref", "--short", "-q", "HEAD")
    if args.branch_name:
        branch_name = args.branch_name
        get_groupy_branch_session(branch_name)
    else:
        branch_name = get_current_branch()
        get_session()

    # Uncommitted changes are only lost when the branch is the current branch
    is_current = branch_name == current_branch
    changes = get_uncommitted_changes() if is_current else []
    nr_of_commits = get_lost_commit_count(branch_name)
    if not _confirm_loss(
        "abort", changes, nr_of_commits, f"on branch {branch_name}", force=args.force
    ):
        return
    undo_path = abort_branch(branch_name, is_current)
    print(f"Aborted {branch_name}. To undo, run: sh {undo_path.as_posix()}")


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


def _print_error(error, command, verbose):
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
        hint = COMMAND_ERROR_HINTS.get((command, type(error))) or ERROR_HINTS.get(
            type(error)
        )
        if hint:
            lines.append(hint)
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
    elif args.command == "status" and args.all:
        _status_all()
    elif args.command == "status":
        _status()
    elif args.command == "reset":
        _reset(args)
    elif args.command == "switch":
        _switch(args)
    elif args.command == "leave":
        _leave(args)
    elif args.command == "abort":
        _abort(args)
    elif args.command == "callback":
        return _callback(args)
    else:
        print("Please specify a command. Use --help for more information.")
        return 1

    return 0


def run(argv=None):
    # Runs groupy without catching its errors (e.g. for the tests)
    args = _parse_args(argv)
    _setup_logging(args.verbose)
    return _run_command(args)


def main(argv=None):
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
        _print_error(error, args.command, args.verbose)
        return 130
    except Exception as error:
        _print_error(error, args.command, args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
