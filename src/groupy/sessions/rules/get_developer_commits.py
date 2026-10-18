import typing as T

from groupy.sessions.enums import Stages
from groupy.utils.run_git import run_git


def get_developer_commits(tag: str) -> T.List[str]:
    # Returns the commits since the tag that Groupy didn't make, as lines with
    # the short hash and the subject
    log = run_git("log", "--reverse", "--format=%h %s", f"{tag}..HEAD")
    return [
        line
        for line in log.splitlines()
        if not _is_groupy_commit(line.split(" ", 1)[1])
    ]


def _is_groupy_commit(subject: str) -> bool:
    return subject == "groupy init" or any(
        subject.startswith(f"{stage.value}: ") for stage in Stages
    )
