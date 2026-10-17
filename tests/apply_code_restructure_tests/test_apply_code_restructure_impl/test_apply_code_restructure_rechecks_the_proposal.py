from apply_code_restructure_tests.apply_code_restructure_test_env import (
    BOOKS,
    Context,
    TestEnv,
)
from groupy.restructure.actions.propose_code_restructure import (
    CodeRestructureHasProblemsError,
)
from sessions_tests.groupy_test_env import BOOKS_PY

REPORT = "myapp/reports/report.py"

REPORT_PY = """\
def create_report(title):
    return title
"""


def create_env(context: Context):
    return Env(context)


def test_apply_code_restructure_rechecks_the_proposal(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-code-restructure, with a valid proposal for the modules of the
    # base env. Besides the modules of the base env, myapp has
    # myapp/reports/report.py, which was added during the review, and has no
    # proposal.
    if env.step(
        env.create_session_at_apply_code_restructure({REPORT: REPORT_PY}),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should validate the proposal before it changes anything, and
    # raise an error that lists the problem. Also the valid proposal of
    # books.py should not have been applied.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, CodeRestructureHasProblemsError)
        assert "myapp/reports/report.py:create_report: has no code_unit_type" in str(
            env.error
        )
        assert env.commit_messages_since_remembered_head() == []
        assert env.git_status() == ""
        assert env.read_module(BOOKS) == BOOKS_PY
        assert env.session.next_stage == "apply-code-restructure"


class Env(TestEnv):
    pass
