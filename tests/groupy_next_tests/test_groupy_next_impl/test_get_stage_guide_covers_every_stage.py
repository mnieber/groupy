import typing as T

from groupy_next_tests.groupy_next_test_env import Context, TestEnv

from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_stage_guide import StageGuide, get_stage_guide

# A fragment of what to review, per stage
REVIEW_FRAGMENTS = {
    Stages.IDENTIFY_HELPER_FUNCTIONS: ["helper_function_nodes"],
    Stages.ANALYZE_TERMINOLOGY: ["glossary"],
    Stages.PROPOSE_RENAMINGS: ["renamings"],
    Stages.APPLY_RENAMINGS: ["git log -p"],
    Stages.EXTRACT_METHODS: ["extracted"],
    Stages.PROPOSE_MOVE_STEPS_TO_CALLER: ["proposed moves"],
    Stages.APPLY_MOVE_STEPS_TO_CALLER: ["moved steps"],
    Stages.PROPOSE_MODULE_LAYOUT: ["package node files"],
    Stages.PROPOSE_CODE_RESTRUCTURE: ["code_unit_type", "dependency violations"],
    Stages.APPLY_CODE_RESTRUCTURE: ["restructured code"],
}


def create_env(context: Context):
    return Env(context)


def test_get_stage_guide_covers_every_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We get the stage guide of every stage (except done).
    #
    # Every stage should have a description, and say what to review.
    if env.step(
        env.load_stage_guides(),
    ):
        assert set(env.stage_guides) == set(REVIEW_FRAGMENTS)
        for stage, guide in env.stage_guides.items():
            assert guide.description, f"{stage.value} has no description"
            for fragment in REVIEW_FRAGMENTS[stage]:
                assert fragment in guide.review, f"{stage.value}: {fragment}"


class Env(TestEnv):
    def __post_init__(self):
        self.stage_guides: T.Dict[Stages, StageGuide] = {}

    def load_stage_guides(self) -> None:
        self.stage_guides = {
            stage: get_stage_guide(stage) for stage in Stages if stage != Stages.DONE
        }
