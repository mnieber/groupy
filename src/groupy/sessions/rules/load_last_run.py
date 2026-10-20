import typing as T

import yaml

from groupy.sessions.models.last_run import LastRun
from groupy.sessions.rules.get_branch_dir import get_branch_dir


def load_last_run(branch_name: T.Optional[str] = None) -> T.Optional[LastRun]:
    # There is no last run before the first groupy next. Without a branch name,
    # this is the last run of the current branch.
    path = get_branch_dir(branch_name) / "last-run.yaml"
    if not path.exists():
        return None
    return LastRun(**yaml.safe_load(path.read_text()))
