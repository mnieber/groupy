import typing as T

from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.utils.has_git_tag import has_git_tag


def get_branch_tags(branch_name: str) -> T.List[str]:
    # The init tag and the start tags of the branch, in the order of the stages
    stages = [None, *[stage for stage in Stages if stage != Stages.DONE]]
    tags = [get_start_tag(stage, branch_name) for stage in stages]
    return [tag for tag in tags if has_git_tag(tag)]
