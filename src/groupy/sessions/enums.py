from enum import Enum


class Stages(str, Enum):
    GROUP_MODULES = "group-modules"
    IDENTIFY_HELPER_FUNCTIONS = "identify-helper-functions"
    ANALYZE_TERMINOLOGY = "analyze-terminology"
    PROPOSE_RENAMINGS = "propose-renamings"
    APPLY_RENAMINGS = "apply-renamings"
    EXTRACT_METHODS = "extract-methods"
    PROPOSE_MOVE_STEPS_TO_CALLER = "propose-move-steps-to-caller"
    APPLY_MOVE_STEPS_TO_CALLER = "apply-move-steps-to-caller"
    PROPOSE_MODULE_LAYOUT = "propose-module-layout"
    PROPOSE_CODE_RESTRUCTURE = "propose-code-restructure"
    APPLY_CODE_RESTRUCTURE = "apply-code-restructure"
    DONE = "done"


class RunResults(str, Enum):
    RUNNING = "running"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"
