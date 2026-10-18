from pathlib import Path

from groupy.sessions.models.session import get_session


def get_source_root() -> Path:
    return Path(get_session().target_dir)
