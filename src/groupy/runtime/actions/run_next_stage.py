import typing as T

from groupy.concepts.actions.analyze_terminology import analyze_terminology
from groupy.functions.actions.apply_move_steps_to_caller import (
    apply_move_steps_to_caller,
)
from groupy.functions.actions.extract_methods import extract_methods
from groupy.functions.actions.identify_helper_functions import identify_helper_functions
from groupy.functions.actions.propose_move_steps_to_caller import (
    propose_move_steps_to_caller,
)
from groupy.groups.actions.group_modules import group_modules
from groupy.renamings.actions.apply_renamings import apply_renamings
from groupy.renamings.actions.propose_renamings import propose_renamings
from groupy.restructure.actions.apply_code_restructure import apply_code_restructure
from groupy.restructure.actions.propose_code_restructure import propose_code_restructure
from groupy.restructure.actions.propose_module_layout import propose_module_layout
from groupy.sessions.actions.commit_changes import commit_changes
from groupy.sessions.actions.save_last_run import save_last_run
from groupy.sessions.actions.save_session import save_session
from groupy.sessions.enums import RunResults, Stages
from groupy.sessions.models.last_run import LastRun
from groupy.sessions.models.session import get_session
from groupy.sessions.rules.check_working_tree_is_clean import (
    check_working_tree_is_clean,
)
from groupy.sessions.rules.get_current_branch import get_current_branch
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_start_tag import get_start_tag
from groupy.sessions.utils.exceptions import NoGroupFileError
from groupy.utils.format_error import format_error
from groupy.utils.has_git_tag import has_git_tag
from groupy.utils.run_git import run_git

STAGE_ACTIONS: T.Dict[Stages, T.Callable[[], None]] = {
    Stages.GROUP_MODULES: group_modules,
    Stages.IDENTIFY_HELPER_FUNCTIONS: identify_helper_functions,
    Stages.ANALYZE_TERMINOLOGY: analyze_terminology,
    Stages.PROPOSE_RENAMINGS: propose_renamings,
    Stages.APPLY_RENAMINGS: apply_renamings,
    Stages.EXTRACT_METHODS: extract_methods,
    Stages.PROPOSE_MOVE_STEPS_TO_CALLER: propose_move_steps_to_caller,
    Stages.APPLY_MOVE_STEPS_TO_CALLER: apply_move_steps_to_caller,
    Stages.PROPOSE_MODULE_LAYOUT: propose_module_layout,
    Stages.PROPOSE_CODE_RESTRUCTURE: propose_code_restructure,
    Stages.APPLY_CODE_RESTRUCTURE: apply_code_restructure,
}


def run_next_stage() -> T.Optional[Stages]:
    # Returns the stage that finished (none when the refactoring is done). The
    # per-branch files need the current branch.
    get_current_branch()
    session = get_session()
    stage = Stages(session.next_stage)
    if stage == Stages.DONE:
        print("The refactoring is done.")
        return None

    # The first stage creates the group file
    if stage != Stages.GROUP_MODULES and not get_groupy_path("groups.txt").exists():
        raise NoGroupFileError("There is no group file")
    check_working_tree_is_clean()

    # Tag the start of the stage, unless the stage is resumed
    start_tag = get_start_tag(stage)
    if not has_git_tag(start_tag):
        run_git("tag", start_tag)

    # When the stage is interrupted, next_stage is unchanged, so that the next
    # call runs the same stage again
    save_last_run(LastRun(stage=stage.value, result=RunResults.RUNNING.value))
    try:
        STAGE_ACTIONS[stage]()
    except BaseException as error:
        save_last_run(
            LastRun(
                stage=stage.value,
                result=RunResults.INTERRUPTED.value,
                request_id=getattr(error, "groupy_request_id", ""),
                error=format_error(error),
            )
        )
        error.groupy_stage_id = stage.value
        raise

    stages = list(Stages)
    session.next_stage = stages[stages.index(stage) + 1].value
    session.finished_chunks = []
    save_session(session)
    commit_changes(f"{stage.value}: finish the stage")
    save_last_run(LastRun(stage=stage.value, result=RunResults.FINISHED.value))
    return stage
