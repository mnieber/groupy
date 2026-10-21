from apply_move_steps_to_caller_tests.apply_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
)

from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from groupy.functions.actions.apply_move_steps_to_caller import PassiveStepMovesError

REPORT = "myapp/reports/report.py"

REPORT_PY = """\
def create_report(user):
    check_user(user)
    return user.name


def send_report(user):
    return create_report(user)


def check_user(user):
    assert user.is_active
"""


def create_env(context: Context):
    return Env(context)


def test_apply_move_steps_to_caller_rejects_steps_in_a_passive_file(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-move-steps-to-caller. Besides the modules of the base env, myapp
    # has myapp/reports/report.py, which the developer excludes. During the
    # review, the developer has proposed to move the step "Check the user" of
    # create_report to its caller.
    if env.step(
        env.create_session_at_apply_move_steps_to_caller({REPORT: REPORT_PY}),
        env.set_session_exclude("myapp/reports/**"),
        env.edit_node_file(add_step, REPORT, "create_report", "Check the user"),
        env.edit_node_file(
            add_step_to_move_to_caller, REPORT, "create_report", "Check the user"
        ),
        env.commit_all("propose to move steps to the caller"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should raise an error that lists the step to move in the passive
    # file, before it makes any RFR.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, PassiveStepMovesError)
        assert f"{REPORT}:create_report: Check the user" in str(env.error)
        assert env.rfr_ids() == []
        assert env.commit_messages_since_remembered_head() == []
        assert env.read_module(REPORT) == REPORT_PY
        assert env.session.next_stage == "apply-move-steps-to-caller"


class Env(TestEnv):
    pass
