from groupy_next_tests.groupy_next_test_env import callback
from propose_renamings_tests.propose_renamings_test_env import (
    RETRY_RFA_ID,
    RFA_ID,
    Context,
    TestEnv,
)

SUMMARY = "myapp/reports/summary.py"

SUMMARY_PY = """\
def summarize(title):
    return title
"""


def create_env(context: Context):
    return Env(context)


def test_propose_renamings_retries_a_renaming_in_a_passive_file(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-renamings. Besides the modules of the base env, myapp has the
    # reports package, which the developer excludes. By mistake, the RFA of the
    # chunk proposes to rename summarize in the passive summary module. The
    # follow-up RFA withdraws the renaming.
    if env.step(
        env.create_session_at_propose_renamings(
            {"myapp/reports/__init__.py": "", SUMMARY: SUMMARY_PY}
        ),
        env.set_session_exclude("myapp/reports/**"),
        env.script_rfa(
            RFA_ID,
            callback(
                "set_rename_to",
                module_name=SUMMARY,
                location="summarize",
                new_name="summarize_report",
            ),
        ),
        env.script_rfa(
            RETRY_RFA_ID,
            callback(
                "set_rename_to",
                module_name=SUMMARY,
                location="summarize",
                new_name=None,
            ),
        ),
    ):
        pass

    # We run groupy next.
    #
    # The renaming in the passive file should be a conflict, so Groupy should
    # make a follow-up RFA that lists it. After the follow-up RFA, the stage
    # should finish.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.rfa_ids() == [RFA_ID, RETRY_RFA_ID]
        assert env.rfa(RETRY_RFA_ID).context["renaming_conflicts"] == [
            f"{SUMMARY}:summarize: is in a passive file"
        ]
        assert env.session.next_stage == "apply-renamings"


class Env(TestEnv):
    pass
