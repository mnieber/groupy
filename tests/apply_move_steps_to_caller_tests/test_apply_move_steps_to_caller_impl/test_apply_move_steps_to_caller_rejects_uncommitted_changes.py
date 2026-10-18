from apply_move_steps_to_caller_tests.apply_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
)
from groupy_next_tests.groupy_next_test_env import callback, file_write

from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from groupy.functions.actions.apply_move_steps_to_caller import (
    UncommittedRefactoringError,
)

REPORTS = "myapp/reports.py"

RFR_ID = "apply-move-steps-to-caller/group-1/chunk-1"

REPORTS_PY = """\
def create_report(user):
    check_user(user)
    return user.name


def send_report(user):
    return create_report(user)


def check_user(user):
    assert user.is_active
"""

MOVED_REPORTS_PY = """\
def create_report(user):
    return user.name


def send_report(user):
    check_user(user)
    return create_report(user)


def check_user(user):
    assert user.is_active
"""


def create_env(context: Context):
    return Env(context)


def test_apply_move_steps_to_caller_rejects_uncommitted_changes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-move-steps-to-caller. Besides the modules of the base env, myapp has
    # reports.py, with the proposal to move the step "Check the user" of
    # create_report to its caller. The RFR of group-1 moves the check of the
    # user to send_report, but forgets to call commit_refactoring.
    if env.step(
        env.create_session_at_apply_move_steps_to_caller({REPORTS: REPORTS_PY}),
        env.edit_node_file(add_step, REPORTS, "create_report", "Check the user"),
        env.edit_node_file(
            add_step_to_move_to_caller, REPORTS, "create_report", "Check the user"
        ),
        env.commit_all("propose to move steps to the caller"),
        env.script_rfr(
            RFR_ID,
            file_write(REPORTS, MOVED_REPORTS_PY),
            callback(
                "remove_step", module_name=REPORTS, location="create_report", index=0
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # After the RFR, Groupy should find the uncommitted changes, discard
    # them (also the edit of the node file), and raise an error, which
    # interrupts the stage.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
        env.load_module_node(REPORTS),
    ):
        assert isinstance(env.error, UncommittedRefactoringError)
        assert env.commit_messages_since_remembered_head() == []
        assert env.git_status() == ""
        assert env.read_module(REPORTS) == REPORTS_PY
        assert env.function_node("create_report").steps == ["Check the user"]
        assert env.function_node("create_report").steps_to_move_to_caller == [
            "Check the user"
        ]
        assert env.session.next_stage == "apply-move-steps-to-caller"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
