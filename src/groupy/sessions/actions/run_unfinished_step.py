import typing as T

from groupy.sessions.actions.commit_stage_changes import commit_stage_changes
from groupy.sessions.actions.save_session import save_session
from groupy.sessions.enums import Stages
from groupy.sessions.models.session import get_session


def run_unfinished_step(
    stage: Stages, step_id: str, run_step: T.Callable[[str], None]
) -> None:
    # A step (e.g. a chunk) is identified by the id <stage-id>/<step-id> of its
    # Claude request. A finished step is skipped, so that an interrupted stage can
    # resume.
    session = get_session()
    request_id = f"{stage.value}/{step_id}"
    if request_id in session.finished_chunks:
        return
    try:
        run_step(request_id)
    except BaseException as error:
        # Lets the developer know where the stage was interrupted
        if not hasattr(error, "groupy_request_id"):
            error.groupy_request_id = request_id
        raise
    session.finished_chunks.append(request_id)
    save_session(session)
    commit_stage_changes(f"finish {step_id}")
