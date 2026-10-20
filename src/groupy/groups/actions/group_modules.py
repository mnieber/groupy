from groupy.groups.actions.create_group_file import create_group_file
from groupy.sessions.actions.commit_stage_changes import commit_stage_changes
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config
from groupy.utils.print_progress import print_progress


def group_modules() -> None:
    print_progress(Stages.GROUP_MODULES.value)
    config = load_config(get_groupy_path("config.yaml"))
    create_group_file(get_source_root(), config, get_groupy_path("groups.txt"))
    commit_stage_changes("create the group file")
