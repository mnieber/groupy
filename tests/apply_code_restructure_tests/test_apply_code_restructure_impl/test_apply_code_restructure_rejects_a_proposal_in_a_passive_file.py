from apply_code_restructure_tests.apply_code_restructure_test_env import (
    BOOKS,
    Context,
    TestEnv,
)
from sessions_tests.groupy_test_env import BOOKS_PY

from groupy.nodes.actions.set_code_unit_type import set_code_unit_type
from groupy.restructure.actions.propose_code_restructure import (
    CodeRestructureHasProblemsError,
)

REPORT = "myapp/reports/report.py"

REPORT_PY = """\
def create_report(title):
    return title
"""


def create_env(context: Context):
    return Env(context)


def test_apply_code_restructure_rejects_a_proposal_in_a_passive_file(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-code-restructure, with a valid proposal for the modules of the
    # base env. Besides the modules of the base env, myapp has
    # myapp/reports/report.py, which the developer excludes. During the
    # review, the developer has added a code unit type to create_report.
    if env.step(
        env.create_session_at_apply_code_restructure({REPORT: REPORT_PY}),
        env.set_session_exclude("myapp/reports/**"),
        env.edit_node_file(set_code_unit_type, REPORT, "create_report", "action"),
        env.commit_all("review the proposal"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should raise an error that lists the proposal in the passive
    # file as a problem, before it changes anything.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, CodeRestructureHasProblemsError)
        assert f"{REPORT}:create_report: is in a passive file" in str(env.error)
        assert env.commit_messages_since_remembered_head() == []
        assert env.git_status() == ""
        assert env.read_module(BOOKS) == BOOKS_PY
        assert env.session.next_stage == "apply-code-restructure"


class Env(TestEnv):
    pass
