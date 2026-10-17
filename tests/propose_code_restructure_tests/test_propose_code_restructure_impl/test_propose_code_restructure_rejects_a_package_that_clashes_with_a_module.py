from groupy.restructure.actions.propose_code_restructure import (
    CodeRestructureHasProblemsError,
)
from groupy_next_tests.groupy_next_test_env import callback
from propose_code_restructure_tests.propose_code_restructure_test_env import (
    REPORTS_RETRY_RFA_ID,
    REPORTS_RFA_ID,
    Context,
    TestEnv,
)

ENUMS = "myapp/reports/enums.py"
REPORT = "myapp/reports/report.py"

ENUMS_PY = """\
import enum


class ReportKind(enum.Enum):
    MARKDOWN = "markdown"
"""

REPORT_PY = """\
from myapp.reports.enums import ReportKind


def list_kinds():
    return [kind.value for kind in ReportKind]
"""

# The RFA of the chunk keeps ReportKind in enums.py, and moves list_kinds to
# a util in the package myapp/reports/enums.
CHUNK_CALLBACKS = [
    callback(
        "set_code_unit_type",
        module_name=ENUMS,
        location="ReportKind",
        code_unit_type="enum",
    ),
    callback(
        "set_code_unit_type",
        module_name=REPORT,
        location="list_kinds",
        code_unit_type="util",
    ),
    callback(
        "set_move_to_file",
        module_name=REPORT,
        location="list_kinds",
        move_to_file="myapp/reports/enums/utils/list_kinds.py",
    ),
]


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_rejects_a_package_that_clashes_with_a_module(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-code-restructure. Besides the modules of the base env, myapp
    # has myapp/reports/enums.py and myapp/reports/report.py (both in
    # group-3). The RFAs of the base modules make a valid proposal. The RFA
    # of group-3 keeps enums.py, and moves list_kinds to the package
    # myapp/reports/enums. The follow-up RFA does nothing.
    if env.step(
        env.create_session_at_propose_code_restructure(
            {ENUMS: ENUMS_PY, REPORT: REPORT_PY}
        ),
        env.script_base_modules(),
        env.script_rfa(REPORTS_RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(REPORTS_RETRY_RFA_ID),
    ):
        pass

    # We run groupy next.
    #
    # Python cannot import both the module myapp/reports/enums.py and the
    # package myapp/reports/enums, so Groupy should raise an error that
    # names both.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
    ):
        assert isinstance(env.error, CodeRestructureHasProblemsError)
        assert (
            "myapp/reports/report.py:list_kinds: the target package"
            " myapp/reports/enums clashes with the module myapp/reports/enums.py"
            in str(env.error)
        )


class Env(TestEnv):
    pass
