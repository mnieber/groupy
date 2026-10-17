from groupy.functions.actions.commit_refactoring import (
    RefactoringDoesNotParseError,
)
from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from groupy_next_tests.groupy_next_test_env import callback, file_write
from apply_move_steps_to_caller_tests.apply_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
)

REPORTS = "myapp/reports.py"

RFR_ID = "apply-move-steps-to-caller/group-1/chunk-1"

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

# The text of reports.py after the first move.
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

# The text of reports.py after the second move, which breaks the syntax.
BROKEN_REPORTS_PY = """\
def create_report(user):
    return user.name


def send_report(user):
    check_user(user)
    log_user(user
    return create_report(user)


def check_user(user):
    assert user.is_active


def log_user(user):
    print(user.name)
"""


def create_env(context: Context):
    return Env(context)


def test_commit_refactoring_rejects_code_that_does_not_parse(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-move-steps-to-caller. Besides the modules of the base env, myapp has
    # reports.py, with the proposals to move the steps "Check the user" and
    # "Log the user" of create_report to its caller. The RFR of group-1 moves
    # the two calls to send_report, and commits after each move. The second
    # move breaks the syntax. (For brevity, the RFR does not update the
    # steps.)
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
            callback("commit_refactoring", description="Move the check"),
            file_write(REPORTS, BROKEN_REPORTS_PY),
            callback("commit_refactoring", description="Move the log"),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # The first move should be committed. For the second move, Groupy should
    # raise an error that names the module, and discard the changes, which
    # interrupts the stage.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, RefactoringDoesNotParseError)
        assert REPORTS in str(env.error)
        assert env.commit_messages_since_remembered_head() == [
            "apply-move-steps-to-caller: Move the check",
        ]
        assert env.git_status() == ""
        assert env.read_module(REPORTS) == CHECK_MOVED_REPORTS_PY
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
