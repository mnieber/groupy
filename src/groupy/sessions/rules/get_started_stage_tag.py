import typing as T

from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.sessions.utils.exceptions import StageNotStartedError
from groupy.utils.has_git_tag import has_git_tag


def get_started_stage_tag(
    stage: T.Optional[Stages], branch_name: T.Optional[str] = None
) -> str:
    # Without a stage, this is the tag of the start of the session, which has
    # always started
    tag = get_start_tag(stage, branch_name)
    if not has_git_tag(tag):
        raise StageNotStartedError(f"{stage.value} has not started")
    return tag
