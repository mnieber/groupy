from groupy_next_tests.groupy_next_test_env import callback
from propose_code_restructure_tests.propose_code_restructure_test_env import (
    BOOKS_CALLBACKS,
    CHAPTERS_CALLBACKS,
    REPORTS_RETRY_RFA_ID,
    REPORTS_RFA_ID,
    Context,
    TestEnv,
    commit_messages,
)

REPORT = "myapp/reports/report.py"

REPORT_PY = """\
class Report:
    def __init__(self, title):
        self.title = title


def create_report(title):
    return Report(title)


def count_reports(reports):
    return len(reports)
"""

# The RFA of the chunk puts the model Report in a rules dir, and forgets
# count_reports.
CHUNK_CALLBACKS = [
    callback(
        "set_rename_to",
        module_name=REPORT,
        location="@module",
        new_name="myapp/reports/actions/create_report.py",
    ),
    callback(
        "set_code_unit_type",
        module_name=REPORT,
        location="create_report",
        code_unit_type="action",
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
        move_to_file="myapp/reports/rules/report.py",
    ),
]

# The follow-up RFA fixes the problems.
RETRY_CALLBACKS = [
    callback(
        "set_move_to_file",
        module_name=REPORT,
        location="Report",
        move_to_file="myapp/reports/models/report.py",
    ),
    callback(
        "set_code_unit_type",
        module_name=REPORT,
        location="count_reports",
        code_unit_type="rule",
    ),
    callback(
        "set_move_to_file",
        module_name=REPORT,
        location="count_reports",
        move_to_file="myapp/reports/rules/count_reports.py",
    ),
]


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_retries_problems(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-code-restructure. Besides the modules of the base env, myapp
    # has myapp/reports/report.py (in group-3). The RFAs of the base modules
    # make a valid proposal. The RFA of group-3 makes a proposal with
    # problems, and the follow-up RFA fixes them.
    if env.step(
        env.create_session_at_propose_code_restructure({REPORT: REPORT_PY}),
        env.script_base_modules(),
        env.script_rfa(REPORTS_RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(REPORTS_RETRY_RFA_ID, *RETRY_CALLBACKS),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # After the RFA of group-3, Groupy should have made a follow-up RFA for
    # the problems, and then finished the chunk and the stage.
    if env.step(
        env.run_groupy_next(),
    ):
        assert env.rfa_ids()[2:] == [REPORTS_RFA_ID, REPORTS_RETRY_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(BOOKS_CALLBACKS),
            "propose-code-restructure: finish group-1/chunk-1",
            *commit_messages(CHAPTERS_CALLBACKS),
            "propose-code-restructure: finish group-2/chunk-1",
            *commit_messages(CHUNK_CALLBACKS),
            *commit_messages(RETRY_CALLBACKS),
            "propose-code-restructure: finish group-3/chunk-1",
            "propose-code-restructure: finish the stage",
        ]

    # We look at the context of the follow-up RFA.
    #
    # It should list the problems, sorted: the model that does not follow
    # the location rule of models, and the node without a code_unit_type.
    if env.step():
        assert env.rfa(REPORTS_RETRY_RFA_ID).context["restructure_problems"] == [
            "myapp/reports/report.py:Report: a model goes to"
            " <package>/models/report.py, not myapp/reports/rules/report.py",
            "myapp/reports/report.py:count_reports: has no code_unit_type",
        ]


class Env(TestEnv):
    pass
