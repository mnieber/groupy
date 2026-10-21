import typing as T
from pathlib import Path

from dataclassy import dataclass

from groupy.nodes.actions.create_node_files import create_node_files
from groupy.sessions.actions.commit_changes import commit_changes
from groupy.sessions.actions.save_config import save_config
from groupy.sessions.actions.save_session import save_session
from groupy.sessions.enums import Stages
from groupy.sessions.models.config import Config
from groupy.sessions.models.session import Session, reset_session
from groupy.sessions.rules.check_branch_dirs_are_ignored import (
    check_branch_dirs_are_ignored,
)
from groupy.sessions.rules.check_working_tree_is_clean import (
    check_working_tree_is_clean,
)
from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.sessions.rules.get_branch_tags import get_branch_tags
from groupy.sessions.rules.get_current_branch import get_current_branch
from groupy.sessions.rules.get_groupy_branch_session import (
    get_groupy_branch_session,
)
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_new_branch_name import get_new_branch_name
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.sessions.rules.get_started_stage_tag import get_started_stage_tag
from groupy.utils.has_git_branch import has_git_branch
from groupy.utils.run_git import run_git


@dataclass
class InitSessionForm:
    target_dir: str = ""
    branch_name: T.Optional[str] = None
    base_branch: str = "main"
    # The stage (or init) that the new branch starts from, on from_branch (by
    # default the current branch)
    from_stage: str = ""
    from_branch: str = ""
    exclude: T.List[str] = []


def init_session(form: InitSessionForm) -> str:
    # Returns the name of the new branch. All checks come before any change to
    # the repo.
    check_working_tree_is_clean()
    if form.from_stage:
        from_branch = form.from_branch or get_current_branch()
        get_groupy_branch_session(from_branch)
        stage = None if form.from_stage == "init" else Stages(form.from_stage)
        start_point = get_started_stage_tag(stage, from_branch)
    elif not has_git_branch(form.base_branch):
        raise NoBaseBranchError(f"The base branch {form.base_branch} doesn't exist")
    else:
        start_point = form.base_branch
    branch_name = form.branch_name or get_new_branch_name()
    if form.branch_name:
        _check_branch_name_is_new(branch_name)
    check_branch_dirs_are_ignored(branch_name)

    # The new branch never starts from the current branch, unless it starts
    # from a stage of the current branch
    run_git("checkout", "-b", branch_name, start_point)
    get_branch_dir(branch_name).mkdir(parents=True, exist_ok=True)
    reset_session()
    if form.from_stage:
        _copy_tags(from_branch, branch_name, stage)
    else:
        _create_session(form, branch_name)
    return branch_name


def _check_branch_name_is_new(branch_name: str) -> None:
    # The per-branch dir of a deleted branch still counts, so that a branch name
    # is never reused
    if has_git_branch(branch_name) or get_branch_dir(branch_name).exists():
        raise BranchExistsError(f"The branch {branch_name} already exists")


def _create_session(form: InitSessionForm, branch_name: str) -> None:
    save_session(
        Session(
            next_stage=Stages.GROUP_MODULES.value,
            target_dir=form.target_dir,
            base_branch=form.base_branch,
            exclude=form.exclude,
        )
    )

    # An existing config file is kept
    config_path = get_groupy_path("config.yaml")
    if not config_path.exists():
        save_config(Config(), config_path)

    # Create the source map. The modules are grouped in the first stage, so that
    # the developer can change the grouping strategy first.
    create_node_files(Path(form.target_dir))
    commit_changes("groupy init")
    run_git("tag", get_start_tag(branch_name=branch_name))


def _copy_tags(
    from_branch: str, branch_name: str, last_stage: T.Optional[Stages]
) -> None:
    # Copies the init tag and the start tags up to and including the last stage,
    # so that groupy reset works on the new branch
    last_tag = get_start_tag(last_stage, from_branch)
    for tag in get_branch_tags(from_branch):
        stage_part = tag[len(f"groupy/{from_branch}/") :]
        run_git("tag", f"groupy/{branch_name}/{stage_part}", f"{tag}^{{commit}}")
        if tag == last_tag:
            break


class BranchExistsError(Exception):
    pass


class NoBaseBranchError(Exception):
    pass
