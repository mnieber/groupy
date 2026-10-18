import typing as T

from groupy.sessions.enums import Stages


def get_start_tag(stage: T.Optional[Stages] = None) -> str:
    # Without a stage, this is the tag of the start of the session
    if stage is None:
        return "groupy/init"
    return f"groupy/{stage.value}/start"
