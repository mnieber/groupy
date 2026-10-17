from breaker.claude_requests.actions.run_callback import CallbackNotAllowedError
from breaker.functions.actions.add_step import add_step
from breaker.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from breaker_next_tests.breaker_next_test_env import callback
from apply_move_steps_to_caller_tests.apply_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
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


def create_env(context: Context):
    return Env(context)


def test_apply_move_steps_to_caller_rejects_a_refactoring_callback(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-move-steps-to-caller. Besides the modules of the base env, myapp has
    # reports.py, with the proposal to move the step "Check the user" of
    # create_report to its caller. The RFR of group-1 calls extract_method,
    # which makes an RFR of its own.
    if env.step(
        env.create_session_at_apply_move_steps_to_caller({REPORTS: REPORTS_PY}),
        env.edit_node_file(add_step, REPORTS, "create_report", "Check the user"),
        env.edit_node_file(
            add_step_to_move_to_caller, REPORTS, "create_report", "Check the user"
        ),
        env.commit_all("propose to move steps to the caller"),
        env.script_rfr(
            RFR_ID,
            callback(
                "extract_method",
                module_name=REPORTS,
                location="create_report",
                new_name="get_name",
                description="Get the name of the user",
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # In an RFR, only the node file edits and commit_refactoring are allowed,
    # so Breaker should raise an error that names the callback, which
    # interrupts the stage.
    if env.step(
        env.catch_error(env.run_breaker, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, CallbackNotAllowedError)
        assert "extract_method" in str(env.error)
        assert env.rfr_ids() == [RFR_ID]
        assert env.commit_messages_since_remembered_head() == []
        assert env.git_status() == ""
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
