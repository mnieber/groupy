from breaker.functions.actions.add_step import add_step
from breaker_next_tests.breaker_next_test_env import callback
from propose_move_steps_to_caller_tests.propose_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
)

REPORTS = "myapp/reports.py"

RFA_ID = "propose-move-steps-to-caller/group-1/chunk-1"

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


def create_env(context: Context):
    return Env(context)


def test_propose_move_steps_to_caller_records_steps_to_move(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-move-steps-to-caller. Besides the modules of the base env, myapp
    # has reports.py, where create_report checks the user before it formats
    # the report. send_report is the only caller of create_report. With the
    # package grouping strategy, the modules of myapp are in group-1, and the
    # modules of myapp/chapters (which have no candidates) are in group-2.
    # The RFA of group-1 proposes to move the check of the user to the
    # caller.
    if env.step(
        env.create_session_at_propose_move_steps_to_caller({REPORTS: REPORTS_PY}),
        env.edit_node_file(add_step, REPORTS, "create_report", "Check the user"),
        env.edit_node_file(add_step, REPORTS, "create_report", "Format the stats"),
        env.commit_all("extract methods"),
        env.script_rfa(
            RFA_ID,
            callback(
                "add_step_to_move_to_caller",
                module_name=REPORTS,
                location="create_report",
                step="Check the user",
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # Breaker should have made an RFA for group-1 only, committed after the
    # callback, and finished both chunks and the stage.
    if env.step(
        env.run_breaker("next"),
    ):
        assert env.rfa_ids() == [RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            "propose-move-steps-to-caller: add_step_to_move_to_caller",
            "propose-move-steps-to-caller: finish group-1/chunk-1",
            "propose-move-steps-to-caller: finish group-2/chunk-1",
            "propose-move-steps-to-caller: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the context of the RFA.
    #
    # It should list the candidates (the functions whose callers are all
    # functions or methods with certain edges), sorted by location, with the
    # source of the modules of the chunk and of the callers.
    if env.step():
        rfa_context = env.rfa(RFA_ID).context
        assert rfa_context["move_step_candidates"] == [
            "myapp/books.py:Book.__init__",
            "myapp/books.py:_normalize_title",
            "myapp/reports.py:_format_stats",
            "myapp/reports.py:check_user",
            "myapp/reports.py:create_report",
        ]
        assert rfa_context["module_sources"][REPORTS] == REPORTS_PY
        assert rfa_context["caller_sources"]["myapp/reports.py:send_report"] == (
            "def send_report(user):\n"
            "    text = create_report(user)\n"
            "    return text"
        )

    # We look at reports.py and its node file.
    #
    # The proposal should be recorded in the node of create_report. The
    # source should be unchanged, so that the developer can review the
    # proposals before they are applied.
    if env.step(
        env.load_module_node(REPORTS),
    ):
        create_report_node = env.function_node("create_report")
        assert create_report_node.steps_to_move_to_caller == ["Check the user"]
        assert create_report_node.steps == ["Check the user", "Format the stats"]
        assert env.read_module(REPORTS) == REPORTS_PY

    # We look at the session.
    #
    # The next stage should be apply-move-steps-to-caller.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "apply-move-steps-to-caller"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
