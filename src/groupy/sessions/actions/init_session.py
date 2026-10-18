from pathlib import Path

from groupy.groups.actions.create_group_file import create_group_file
from groupy.nodes.actions.create_node_files import create_node_files
from groupy.sessions.actions.commit_changes import commit_changes
from groupy.sessions.actions.exclude_groupy_file_from_git import (
    exclude_groupy_file_from_git,
)
from groupy.sessions.actions.save_config import save_config
from groupy.sessions.actions.save_session import save_session
from groupy.sessions.enums import Stages
from groupy.sessions.models.config import Config
from groupy.sessions.models.session import Session, reset_session
from groupy.sessions.rules.check_working_tree_is_clean import (
    check_working_tree_is_clean,
)
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.sessions.rules.load_config import load_config
from groupy.utils.run_git import run_git


def init_session(target_dir: str, branch_name: str) -> None:
    if get_groupy_path("session.yaml").exists():
        raise SessionExistsError("There already is a groupy session")
    check_working_tree_is_clean()

    run_git("checkout", "-b", branch_name)
    exclude_groupy_file_from_git("call-graph.yaml")
    exclude_groupy_file_from_git("last-run.yaml")
    exclude_groupy_file_from_git("logs")
    exclude_groupy_file_from_git("requests")
    reset_session()
    save_session(
        Session(
            next_stage=Stages.IDENTIFY_HELPER_FUNCTIONS.value, target_dir=target_dir
        )
    )

    # An existing config file is kept
    config_path = get_groupy_path("config.yaml")
    if not config_path.exists():
        save_config(Config(), config_path)

    # Create the source map and the group file
    source_root = Path(target_dir)
    create_node_files(source_root)
    create_group_file(
        source_root, load_config(config_path), get_groupy_path("groups.txt")
    )
    commit_changes("groupy init")
    run_git("tag", get_start_tag())


class SessionExistsError(Exception):
    pass
