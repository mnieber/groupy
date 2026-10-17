from breaker.functions.actions.add_step import add_step
from breaker.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from breaker_next_tests.breaker_next_test_env import callback, file_write
from apply_move_steps_to_caller_tests.apply_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
)

REPORTS = "myapp/reports.py"

RFR_ID = "apply-move-steps-to-caller/group-1/chunk-1"

REPORTS_PY = """\
def create_report(user):
    check_user(user)
    lines = _format_stats(user.stats)
    return "\\n".join(lines)


def send_report(user):
    text = create_report(user)
    return text


def _format_stats(stats):
    return [f"{stat.name}: {stat.value}" for stat in stats]


def check_user(user):
    if not user.is_active:
        raise ValueError("The user is not active")
"""

# The text of reports.py after the RFR moved the check of the user to
# send_report.
MOVED_REPORTS_PY = """\
def create_report(user):
    lines = _format_stats(user.stats)
    return "\\n".join(lines)


def send_report(user):
    check_user(user)
    text = create_report(user)
    return text


def _format_stats(stats):
    return [f"{stat.name}: {stat.value}" for stat in stats]


def check_user(user):
    if not user.is_active:
        raise ValueError("The user is not active")
"""


def create_env(context: Context):
    return Env(context)


def test_apply_move_steps_to_caller_moves_a_step(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-move-steps-to-caller. Besides the modules of the base env, myapp has
    # reports.py, where create_report checks the user before it formats the
    # report. send_report is the only caller of create_report, and the
    # propose-move-steps-to-caller stage has proposed to move the step
    # "Check the user" of create_report to its caller. With the package
    # grouping strategy, the modules of myapp are in group-1, and the modules
    # of myapp/chapters (which have no proposed moves) are in group-2.
    #
    # The RFR of group-1 moves the check of the user to send_report: it
    # changes the source, updates the steps of both functions (via actions)
    # and commits the refactoring. Removing the step from create_report also
    # removes it from the steps to move.
    if env.step(
        env.create_session_at_apply_move_steps_to_caller({REPORTS: REPORTS_PY}),
        env.edit_node_file(add_step, REPORTS, "create_report", "Check the user"),
        env.edit_node_file(add_step, REPORTS, "create_report", "Format the stats"),
        env.edit_node_file(add_step, REPORTS, "send_report", "Create the report"),
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
            callback(
                "add_step",
                module_name=REPORTS,
                location="send_report",
                step="Check the user",
                index=0,
            ),
            callback(
                "commit_refactoring",
                description="Move the check of the user to send_report",
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # Breaker should have made an RFR for group-1 only. The callbacks in the
    # RFR should not have committed by themselves: commit_refactoring should
    # have committed the source and the node file together.
    if env.step(
        env.run_breaker("next"),
    ):
        assert env.rfr_ids() == [RFR_ID]
        assert env.rfa_ids() == []
        assert env.commit_messages_since_remembered_head() == [
            "apply-move-steps-to-caller: Move the check of the user to send_report",
            "apply-move-steps-to-caller: finish group-1/chunk-1",
            "apply-move-steps-to-caller: finish group-2/chunk-1",
            "apply-move-steps-to-caller: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the context of the RFR.
    #
    # It should list the steps to move (as `<module>:<location>: <step>`),
    # with the source of the modules of the chunk and of the callers of the
    # functions whose steps move.
    if env.step():
        rfr_context = env.rfr(RFR_ID).context
        assert rfr_context["steps_to_move_to_caller"] == [
            "myapp/reports.py:create_report: Check the user"
        ]
        assert rfr_context["module_sources"][REPORTS] == REPORTS_PY
        assert rfr_context["caller_sources"]["myapp/reports.py:send_report"] == (
            "def send_report(user):\n"
            "    text = create_report(user)\n"
            "    return text"
        )

    # We look at reports.py and its node file.
    #
    # The step should have moved from create_report to send_report.
    if env.step(
        env.load_module_node(REPORTS),
    ):
        assert env.read_module(REPORTS) == MOVED_REPORTS_PY
        assert env.function_node("create_report").steps == ["Format the stats"]
        assert env.function_node("create_report").steps_to_move_to_caller == []
        assert env.function_node("send_report").steps == [
            "Check the user",
            "Create the report",
        ]

    # We look at the session.
    #
    # The next stage should be propose-module-layout.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "propose-module-layout"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
