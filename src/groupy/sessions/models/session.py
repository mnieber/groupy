import typing as T

import yaml
from dataclassy import dataclass

from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.utils.exceptions import NoSessionError


@dataclass
class Session:
    next_stage: str
    target_dir: str
    base_branch: str
    finished_chunks: T.List[str] = []


_session: T.Optional[Session] = None


def get_session() -> Session:
    # The session is loaded from the session file once
    global _session
    if _session is None:
        session_path = get_groupy_path("session.yaml")
        if not session_path.exists():
            raise NoSessionError("There is no groupy session: run groupy init first")
        _session = Session(**yaml.safe_load(session_path.read_text()))
    return _session


def reset_session() -> None:
    global _session
    _session = None
