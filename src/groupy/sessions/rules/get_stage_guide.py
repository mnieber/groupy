from groupy.sessions.enums import Stages
from groupy.sessions.models.stage_guide import StageGuide

STAGE_GUIDES = {
    Stages.GROUP_MODULES: StageGuide(
        description="divides the modules into groups, with the grouping strategy of "
        "the config file",
        review="the groups in the group file (.groupy/groups.txt)",
    ),
    Stages.IDENTIFY_HELPER_FUNCTIONS: StageGuide(
        description="nests each helper function under the function that it serves",
        review="the nesting of the helper functions (helper_function_nodes in the "
        "node files) and their new names",
    ),
    Stages.ANALYZE_TERMINOLOGY: StageGuide(
        description="analyzes the concepts and terms of the code, and fills the "
        "glossary",
        review="the glossary (give entries with the same name distinct names), and "
        "the concepts, local terms and abbreviations in the node files",
    ),
    Stages.PROPOSE_RENAMINGS: StageGuide(
        description="proposes renamings that follow the glossary",
        review="the proposed renamings in the node files",
    ),
    Stages.APPLY_RENAMINGS: StageGuide(
        description="applies the renamings to the code",
        review="the renamed code (e.g. with git log -p)",
    ),
    Stages.EXTRACT_METHODS: StageGuide(
        description="extracts helper functions from long functions",
        review="the extracted helper functions",
    ),
    Stages.PROPOSE_MOVE_STEPS_TO_CALLER: StageGuide(
        description="proposes to move steps of functions to their callers",
        review="the proposed moves in the node files",
    ),
    Stages.APPLY_MOVE_STEPS_TO_CALLER: StageGuide(
        description="moves the proposed steps to the callers",
        review="the moved steps in the code",
    ),
    Stages.PROPOSE_MODULE_LAYOUT: StageGuide(
        description="proposes the modules of each package",
        review="the proposed modules in the package node files",
    ),
    Stages.PROPOSE_CODE_RESTRUCTURE: StageGuide(
        description="proposes where each code unit goes",
        review="the proposal (code_unit_type, move_to_file and rename_to in the node "
        "files) and the printed dependency violations",
    ),
    Stages.APPLY_CODE_RESTRUCTURE: StageGuide(
        description="restructures the code as proposed",
        review="the restructured code",
    ),
}


def get_stage_guide(stage: Stages) -> StageGuide:
    return STAGE_GUIDES[stage]
