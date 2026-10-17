from groupy_next_tests.groupy_next_test_env import callback
from propose_code_restructure_tests.propose_code_restructure_test_env import (
    REPORTS_RFA_ID,
    Context,
    TestEnv,
)

REPORT = "myapp/reports/report.py"

REPORT_PY = """\
class Report:
    def __init__(self, title):
        self.title = title

    def save(self):
        store_report(self)

    def publish(self):
        send_reminder(self)


def store_report(report):
    print(report.title)


def get_overdue_reports(reports):
    send_reminder(reports[0])
    return reports


def send_reminder(report):
    print("Please read", report.title)
"""


def unit_callbacks(location: str, code_unit_type: str, move_to_file: str):
    """Returns the callbacks that set the code_unit_type and move_to_file of
    the node at the location."""
    return [
        callback(
            "set_code_unit_type",
            module_name=REPORT,
            location=location,
            code_unit_type=code_unit_type,
        ),
        callback(
            "set_move_to_file",
            module_name=REPORT,
            location=location,
            move_to_file=move_to_file,
        ),
    ]


# The RFA of the chunk proposes a model Report, whose method save delegates
# to an action, a rule get_overdue_reports and two actions.
CHUNK_CALLBACKS = [
    *unit_callbacks("Report", "model", "myapp/reports/models/report.py"),
    *unit_callbacks("Report.save", "action", "myapp/reports/actions/save_report.py"),
    *unit_callbacks("store_report", "action", "myapp/reports/actions/store_report.py"),
    *unit_callbacks(
        "get_overdue_reports", "rule", "myapp/reports/rules/get_overdue_reports.py"
    ),
    *unit_callbacks(
        "send_reminder", "action", "myapp/reports/actions/send_reminder.py"
    ),
]


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_reports_dependency_violations(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-code-restructure. Besides the modules of the base env, myapp
    # has myapp/reports/report.py (in group-3). The RFAs of the base modules
    # make a valid proposal. The RFA of group-3 proposes a model Report whose
    # method save delegates to an action, and whose method publish stays.
    if env.step(
        env.create_session_at_propose_code_restructure({REPORT: REPORT_PY}),
        env.script_base_modules(),
        env.script_rfa(REPORTS_RFA_ID, *CHUNK_CALLBACKS),
    ):
        pass

    # We run groupy next.
    #
    # Dependency violations do not block the stage, so Groupy should finish
    # the stage, and print the violations, sorted:
    # - the method publish stays in the model, which calls an action;
    # - the rule get_overdue_reports calls an action.
    # The method save delegates to an action, so its call of the action
    # store_report is judged as a call of an action, which is allowed.
    if env.step(
        env.run_groupy_next(),
        env.load_session(),
    ):
        assert env.output_lines == [
            "The proposed code structure has dependency violations:",
            "myapp/reports/report.py:Report.publish (model) calls"
            " myapp/reports/report.py:send_reminder (action)",
            "myapp/reports/report.py:get_overdue_reports (rule) calls"
            " myapp/reports/report.py:send_reminder (action)",
        ]
        assert env.session.next_stage == "apply-code-restructure"


class Env(TestEnv):
    pass
