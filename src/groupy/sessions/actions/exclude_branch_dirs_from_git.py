from pathlib import Path

from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.utils.run_git import run_git


def exclude_branch_dirs_from_git() -> None:
    # The per-branch dirs (e.g. with the logs) are not committed. They are
    # excluded locally, so that no .gitignore is needed.
    exclude_path = Path(run_git("rev-parse", "--git-path", "info/exclude"))
    line = f"/{get_groupy_path('*').as_posix()}/\n"
    text = exclude_path.read_text() if exclude_path.exists() else ""
    if line not in text.splitlines(keepends=True):
        if text and not text.endswith("\n"):
            text += "\n"
        exclude_path.parent.mkdir(parents=True, exist_ok=True)
        exclude_path.write_text(text + line)
