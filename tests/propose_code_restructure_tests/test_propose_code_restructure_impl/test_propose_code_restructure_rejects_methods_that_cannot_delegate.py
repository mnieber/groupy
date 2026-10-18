from groupy_next_tests.groupy_next_test_env import callback
from propose_code_restructure_tests.propose_code_restructure_test_env import (
    REPORTS_RETRY_RFA_ID,
    REPORTS_RFA_ID,
    Context,
    TestEnv,
)

from groupy.restructure.actions.propose_code_restructure import (
    CodeRestructureHasProblemsError,
)

REPORT = "myapp/reports/report.py"

REPORT_PY = """\
class Base:
    def describe(self):
        return "a report"


class Report(Base):
    def __init__(self, title):
        self.title = title

    def __str__(self):
        return self.title

    @property
    def heading(self):
        return self.title.upper()

    def describe(self):
        return "the report " + self.title

    def extend(self):
        return super().describe() + "!"

    def render(self):
        return "# " + self.heading
"""


def delegate_callbacks(location: str, move_to_file: str):
    """Returns the callbacks that propose that the method at the location
    delegates to a rule in move_to_file."""
    return [
        callback(
            "set_code_unit_type",
            module_name=REPORT,
            location=location,
            code_unit_type="rule",
        ),
        callback(
            "set_move_to_file",
            module_name=REPORT,
            location=location,
            move_to_file=move_to_file,
        ),
    ]


# The RFA of the chunk moves the classes to their model files, and proposes
# that five methods of Report delegate to rules.
CHUNK_CALLBACKS = [
    callback(
        "set_code_unit_type",
        module_name=REPORT,
        location="Base",
        code_unit_type="model",
    ),
    callback(
        "set_move_to_file",
        module_name=REPORT,
        location="Base",
        move_to_file="myapp/reports/models/base.py",
    ),
    callback(
        "set_code_unit_type",
        module_name=REPORT,
        location="Report",
        code_unit_type="model",
    ),
    callback(
        "set_move_to_file",
        module_name=REPORT,
        location="Report",
        move_to_file="myapp/reports/models/report.py",
    ),
    *delegate_callbacks("Report.__str__", "myapp/reports/rules/format_report.py"),
    *delegate_callbacks("Report.heading", "myapp/reports/rules/get_heading.py"),
    *delegate_callbacks("Report.describe", "myapp/reports/rules/describe_report.py"),
    *delegate_callbacks("Report.extend", "myapp/reports/rules/extend_description.py"),
    *delegate_callbacks("Report.render", "myapp/reports/rules/render_report.py"),
]


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_rejects_methods_that_cannot_delegate(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-code-restructure. Besides the modules of the base env, myapp
    # has myapp/reports/report.py (in group-3). The RFAs of the base modules
    # make a valid proposal. The RFA of group-3 proposes that five methods of
    # Report delegate to a rule, and the follow-up RFA does nothing.
    if env.step(
        env.create_session_at_propose_code_restructure({REPORT: REPORT_PY}),
        env.script_base_modules(),
        env.script_rfa(REPORTS_RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(REPORTS_RETRY_RFA_ID),
    ):
        pass

    # We run groupy next.
    #
    # Only render can delegate, so Groupy should raise an error that lists
    # the other four methods with the reason why they cannot delegate.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
    ):
        assert isinstance(env.error, CodeRestructureHasProblemsError)
        for problem in [
            "myapp/reports/report.py:Report.__str__: a dunder method cannot delegate",
            "myapp/reports/report.py:Report.describe: an override of Base.describe"
            " cannot delegate",
            "myapp/reports/report.py:Report.extend: a method that uses super()"
            " cannot delegate",
            "myapp/reports/report.py:Report.heading: a property cannot delegate",
        ]:
            assert problem in str(env.error)
        assert "Report.render" not in str(env.error)


class Env(TestEnv):
    pass
