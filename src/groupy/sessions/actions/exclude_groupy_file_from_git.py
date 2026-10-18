from pathlib import Path

from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.utils.run_git import run_git


def exclude_groupy_file_from_git(file_name: str) -> None:
    # Files that Groupy derives from the code (e.g. the call graph) are not
    # committed. They are excluded locally, so that no .gitignore is needed.
    exclude_path = Path(run_git("rev-parse", "--git-path", "info/exclude"))
    line = f"/{get_groupy_path(file_name).as_posix()}\n"
    text = exclude_path.read_text() if exclude_path.exists() else ""
    if line not in text:
        exclude_path.parent.mkdir(parents=True, exist_ok=True)
        exclude_path.write_text(text + line)
