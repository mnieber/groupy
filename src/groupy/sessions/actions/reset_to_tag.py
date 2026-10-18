from groupy.sessions.enums import Stages
from groupy.sessions.models.session import get_session, reset_session
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.utils.has_git_tag import has_git_tag
from groupy.utils.run_git import run_git


def reset_to_tag(tag: str) -> str:
    # Returns the previous head, so that the reset can be undone
    previous_head = run_git("rev-parse", "HEAD")
    run_git("reset", "--hard", tag)
    run_git("clean", "-fd")
    reset_session()

    # The stages from the next stage on have not started anymore
    stages = list(Stages)
    next_index = stages.index(Stages(get_session().next_stage))
    for stage in stages[next_index:]:
        start_tag = get_start_tag(stage)
        if has_git_tag(start_tag):
            run_git("tag", "-d", start_tag)
    return previous_head
