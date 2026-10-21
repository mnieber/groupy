from groupy_next_tests.groupy_next_test_env import callback
from propose_code_restructure_tests.propose_code_restructure_test_env import (
    BOOKS_CALLBACKS,
    BOOKS_RFA_ID,
    Context,
    TestEnv,
)

from groupy.restructure.actions.propose_code_restructure import (
    CodeRestructureHasProblemsError,
)

REPORT = "myapp/reports/report.py"

REPORT_PY = """\
def create_report(title):
    return title
"""

BOOKS_RETRY_RFA_ID = f"{BOOKS_RFA_ID}/retry-1"

# By mistake, the RFA of books.py also proposes a code unit type for
# create_report, which is in a passive file.
PASSIVE_CALLBACK = callback(
    "set_code_unit_type",
    module_name=REPORT,
    location="create_report",
    code_unit_type="action",
)


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_rejects_a_proposal_in_a_passive_file(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-code-restructure. Besides the modules of the base env, myapp has
    # myapp/reports/report.py (in group-3), which the developer excludes. The
    # RFA of books.py makes a valid proposal, but also a proposal for the
    # passive report module, and the follow-up RFA does not withdraw it.
    if env.step(
        env.create_session_at_propose_code_restructure({REPORT: REPORT_PY}),
        env.set_session_exclude("myapp/reports/**"),
        env.script_base_modules(),
        env.script_rfa(BOOKS_RFA_ID, *BOOKS_CALLBACKS, PASSIVE_CALLBACK),
        env.script_rfa(BOOKS_RETRY_RFA_ID),
    ):
        pass

    # We run groupy next.
    #
    # The proposal in the passive file should be a problem, so Groupy should
    # make a follow-up RFA that lists it, and then raise an error, which
    # interrupts the stage.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, CodeRestructureHasProblemsError)
        assert f"{REPORT}:create_report: is in a passive file" in str(env.error)
        assert env.rfa(BOOKS_RETRY_RFA_ID).context["restructure_problems"] == [
            f"{REPORT}:create_report: is in a passive file"
        ]
        assert env.session.next_stage == "propose-code-restructure"


class Env(TestEnv):
    pass
