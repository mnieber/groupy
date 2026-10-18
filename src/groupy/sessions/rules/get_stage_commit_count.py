from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.utils.run_git import run_git


def get_stage_commit_count(stage: Stages) -> int:
    # Counts the commits since the start of the stage
    return int(run_git("rev-list", "--count", f"{get_start_tag(stage)}..HEAD"))
