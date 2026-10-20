import typing as T

from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_current_branch import get_current_branch


def get_start_tag(
    stage: T.Optional[Stages] = None, branch_name: T.Optional[str] = None
) -> str:
    # Without a stage, this is the tag of the start of the session. Without a
    # branch name, this is the tag of the current branch.
    branch_name = branch_name or get_current_branch()
    if stage is None:
        return f"groupy/{branch_name}/init"
    return f"groupy/{branch_name}/{stage.value}/start"
