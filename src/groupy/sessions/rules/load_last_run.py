import typing as T

import yaml

from groupy.sessions.models.last_run import LastRun
from groupy.sessions.rules.get_groupy_path import get_groupy_path


def load_last_run() -> T.Optional[LastRun]:
    # There is no last run before the first groupy next
    path = get_groupy_path("last-run.yaml")
    if not path.exists():
        return None
    return LastRun(**yaml.safe_load(path.read_text()))
