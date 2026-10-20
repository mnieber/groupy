import shlex
from pathlib import Path

from groupy.sessions.actions.discard_and_checkout import discard_and_checkout
from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.sessions.rules.get_branch_tags import get_branch_tags
from groupy.sessions.rules.get_groupy_branch_session import (
    get_groupy_branch_session,
)
from groupy.utils.run_git import run_git


def abort_branch(branch_name: str, is_current: bool) -> Path:
    # Deletes the branch and its tags, and returns the path of the script that
    # undoes this. The per-branch dir is kept.
    session = get_groupy_branch_session(branch_name)
    tags = get_branch_tags(branch_name)

    # Write the undo script
    lines = [
        f"git branch {shlex.quote(branch_name)} "
        f"{run_git('rev-parse', f'refs/heads/{branch_name}')}"
    ] + [
        f"git tag {shlex.quote(tag)} {run_git('rev-parse', f'{tag}^{{commit}}')}"
        for tag in tags
    ]
    undo_path = get_branch_dir(branch_name) / "undo-abort.sh"
    undo_path.parent.mkdir(parents=True, exist_ok=True)
    undo_path.write_text("\n".join(lines) + "\n")

    # A branch cannot be deleted while it is checked out
    if is_current:
        discard_and_checkout(session.base_branch)
    run_git("branch", "-D", branch_name)
    for tag in tags:
        run_git("tag", "-d", tag)
    return undo_path
