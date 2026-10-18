from apply_move_steps_to_caller_tests.apply_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
)
from groupy_next_tests.groupy_next_test_env import callback, file_write

from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from groupy.functions.actions.apply_move_steps_to_caller import UnappliedStepMovesError

REPORTS = "myapp/reports.py"

RFR_ID = "apply-move-steps-to-caller/group-1/chunk-1"
RETRY_RFR_ID = "apply-move-steps-to-caller/group-1/chunk-1/retry-1"

REPORTS_PY = """\
def create_report(user):
    check_user(user)
    log_user(user)
    return user.name


def send_report(user):
    return create_report(user)


def check_user(user):
    assert user.is_active


def log_user(user):
    print(user.name)
"""

# The text of reports.py after the RFR moved the check of the user.
CHECK_MOVED_REPORTS_PY = """\
def create_report(user):
    log_user(user)
    return user.name


def send_report(user):
    check_user(user)
    return create_report(user)


def check_user(user):
    assert user.is_active


def log_user(user):
    print(user.name)
"""


def create_env(context: Context):
    return Env(context)


def test_apply_move_steps_to_caller_rejects_unapplied_moves(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-move-steps-to-caller. Besides the modules of the base env, myapp
    # has reports.py, with the proposals to move the steps "Check the user"
    # and "Log the user" of create_report to its caller. The RFR of group-1
    # only moves the check of the user, and the follow-up RFR does nothing.
    if env.step(
        env.create_session_at_apply_move_steps_to_caller({REPORTS: REPORTS_PY}),
        env.edit_node_file(add_step, REPORTS, "create_report", "Check the user"),
        env.edit_node_file(add_step, REPORTS, "create_report", "Log the user"),
        env.edit_node_file(
            add_step_to_move_to_caller, REPORTS, "create_report", "Check the user"
        ),
        env.edit_node_file(
            add_step_to_move_to_caller, REPORTS, "create_report", "Log the user"
        ),
        env.commit_all("propose to move steps to the caller"),
        env.script_rfr(
            RFR_ID,
            file_write(REPORTS, CHECK_MOVED_REPORTS_PY),
            callback(
                "remove_step", module_name=REPORTS, location="create_report", index=0
            ),
            callback(
                "add_step",
                module_name=REPORTS,
                location="send_report",
                step="Check the user",
            ),
            callback("commit_refactoring", description="Move the check"),
        ),
        env.script_rfr(RETRY_RFR_ID),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # After the RFR, Groupy should have made a follow-up RFR for the step
    # that was not moved. Since the step is still not moved after the
    # follow-up RFR, Groupy should raise an error that lists it, which
    # interrupts the stage. The move of the check should stay committed.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert env.rfr_ids() == [RFR_ID, RETRY_RFR_ID]
        assert env.rfr(RETRY_RFR_ID).context["steps_to_move_to_caller"] == [
            "myapp/reports.py:create_report: Log the user"
        ]
        assert isinstance(env.error, UnappliedStepMovesError)
        assert "myapp/reports.py:create_report: Log the user" in str(env.error)
        assert env.commit_messages_since_remembered_head() == [
            "apply-move-steps-to-caller: Move the check",
        ]
        assert env.git_status() == ""
        assert env.session.next_stage == "apply-move-steps-to-caller"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
