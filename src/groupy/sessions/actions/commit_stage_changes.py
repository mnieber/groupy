from groupy.sessions.actions.commit_changes import commit_changes
from groupy.sessions.models.session import get_session


def commit_stage_changes(description: str) -> None:
    # The commits of a stage are grouped by the stage id in the message
    commit_changes(f"{get_session().next_stage}: {description}")
