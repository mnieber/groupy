import argparse
import logging
import sys

from groupy.nodes.actions.sync_node_files import sync_node_files
from groupy.runtime.actions.run_next_stage import run_next_stage
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.actions.init_session import init_session

logger = logging.getLogger(__name__)


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

    # Next command
    subparsers.add_parser("next", help="Run the next stage of the session")

    # Sync command
    subparsers.add_parser(
        "sync", help="Update the node files after the source was changed by hand"
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


def main(argv=None):
    args = _parse_args(argv)
    _setup_logging(args.verbose)

    if args.command == "init":
        init_session(args.target_dir, args.branch_name)
    elif args.command == "next":
        run_next_stage()
    elif args.command == "sync":
        _sync()
    else:
        print("Please specify a command. Use --help for more information.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
