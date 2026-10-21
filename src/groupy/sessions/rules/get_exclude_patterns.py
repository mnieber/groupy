import typing as T

from groupy.sessions.models.session import get_session
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.load_config import load_config


def get_exclude_patterns() -> T.List[str]:
    # The union of the patterns in the config file and in the session file
    config = load_config(get_groupy_path("config.yaml"))
    patterns = [*config.exclude, *get_session().exclude]
    return list(dict.fromkeys(patterns))
