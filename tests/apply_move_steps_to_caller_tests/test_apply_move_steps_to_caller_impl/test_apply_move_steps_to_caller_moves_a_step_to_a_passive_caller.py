from apply_move_steps_to_caller_tests.apply_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
)
from groupy_next_tests.groupy_next_test_env import callback, file_write

from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)

REPORTS = "myapp/reports.py"
MAILING = "myapp/mailing.py"

RFR_ID = "apply-move-steps-to-caller/group-1/chunk-1"

REPORTS_PY = """\
def create_report(user):
    check_user(user)
    return user.name


def check_user(user):
    assert user.is_active
"""

MAILING_PY = """\
from myapp.reports import create_report


def send_report(user):
    return create_report(user)
"""

MOVED_REPORTS_PY = """\
def create_report(user):
    return user.name


def check_user(user):
    assert user.is_active
"""

MOVED_MAILING_PY = """\
from myapp.reports import check_user, create_report


def send_report(user):
    check_user(user)
    return create_report(user)
"""


def create_env(context: Context):
    return Env(context)


def test_apply_move_steps_to_caller_moves_a_step_to_a_passive_caller(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-move-steps-to-caller. Besides the modules of the base env, myapp
    # has reports.py and mailing.py, which the developer excludes. The
    # propose-move-steps-to-caller stage has proposed to move the step "Check
    # the user" of create_report to its only caller, send_report, which is in
    # the passive mailing module.
    #
    # The RFR moves the check of the user to send_report: it changes both
    # modules, updates the steps of both functions and commits the
    # refactoring.
    if env.step(
        env.create_session_at_apply_move_steps_to_caller(
            {REPORTS: REPORTS_PY, MAILING: MAILING_PY}
        ),
        env.set_session_exclude(MAILING),
        env.edit_node_file(add_step, REPORTS, "create_report", "Check the user"),
        env.edit_node_file(
            add_step_to_move_to_caller, REPORTS, "create_report", "Check the user"
        ),
        env.commit_all("propose to move steps to the caller"),
        env.script_rfr(
            RFR_ID,
            file_write(REPORTS, MOVED_REPORTS_PY),
            file_write(MAILING, MOVED_MAILING_PY),
            callback(
                "remove_step", module_name=REPORTS, location="create_report", index=0
            ),
            callback(
                "add_step",
                module_name=MAILING,
                location="send_report",
                step="Check the user",
                index=0,
            ),
            callback(
                "commit_refactoring",
                description="Move the check of the user to send_report",
            ),
        ),
    ):
        pass

    # We run groupy next.
    #
    # The context of the RFR should have the source of the passive caller.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.rfr_ids() == [RFR_ID]
        assert f"{MAILING}:send_report" in env.rfr(RFR_ID).context["caller_sources"]

    # We look at mailing.py and its node file.
    #
    # The step should have moved to the passive caller.
    if env.step(
        env.load_module_node(MAILING),
    ):
        assert env.read_module(MAILING) == MOVED_MAILING_PY
        assert env.function_node("send_report").steps == ["Check the user"]


class Env(TestEnv):
    pass
