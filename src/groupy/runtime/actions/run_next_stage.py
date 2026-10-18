import typing as T

from groupy.concepts.actions.analyze_terminology import analyze_terminology
from groupy.functions.actions.identify_helper_functions import (
    identify_helper_functions,
)
from groupy.functions.actions.apply_move_steps_to_caller import (
    apply_move_steps_to_caller,
)
from groupy.functions.actions.extract_methods import extract_methods
from groupy.functions.actions.propose_move_steps_to_caller import (
    propose_move_steps_to_caller,
)
from groupy.renamings.actions.apply_renamings import apply_renamings
from groupy.renamings.actions.propose_renamings import propose_renamings
from groupy.restructure.actions.apply_code_restructure import apply_code_restructure
from groupy.restructure.actions.propose_code_restructure import (
    propose_code_restructure,
)
from groupy.restructure.actions.propose_module_layout import propose_module_layout
from groupy.sessions.actions.commit_changes import commit_changes
from groupy.sessions.actions.save_session import save_session
from groupy.sessions.enums import Stages
from groupy.sessions.models.session import get_session
from groupy.sessions.rules.check_working_tree_is_clean import (
    check_working_tree_is_clean,
)
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.utils.exceptions import NoGroupFileError

STAGE_ACTIONS: T.Dict[Stages, T.Callable[[], None]] = {
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


def run_next_stage() -> None:
    session = get_session()
    stage = Stages(session.next_stage)
    if stage == Stages.DONE:
        print("The refactoring is done.")
        return

    if not get_groupy_path("groups.txt").exists():
        raise NoGroupFileError("There is no group file: run groupy group first")
    check_working_tree_is_clean()

    # When the stage is interrupted, next_stage is unchanged, so that the next
    # call runs the same stage again
    STAGE_ACTIONS[stage]()

    stages = list(Stages)
    session.next_stage = stages[stages.index(stage) + 1].value
    session.finished_chunks = []
    save_session(session)
    commit_changes(f"{stage.value}: finish the stage")
