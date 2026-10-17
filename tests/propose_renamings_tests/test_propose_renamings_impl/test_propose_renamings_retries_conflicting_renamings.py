from groupy_next_tests.groupy_next_test_env import callback
from propose_renamings_tests.propose_renamings_test_env import (
    RETRY_RFA_ID,
    RFA_ID,
    Context,
    TestEnv,
    commit_messages,
)

REPORTS = "myapp/reports.py"

REPORTS_PY = """\
def create_report(user, report):
    title = user.name
    text = report.text
    return title + text


def create_summary(user):
    return user.name


def format_report(report):
    return report.text
"""

# The RFA of the chunk proposes renamings that clash:
# - title -> text clashes with the local variable text;
# - user -> person and report -> person have the same new name;
# - create_summary -> format_report clashes with the function format_report.
CHUNK_CALLBACKS = [
    callback(
        "set_renaming",
        module_name=REPORTS,
        location="create_report",
        name="title",
        new_name="text",
    ),
    callback(
        "set_renaming",
        module_name=REPORTS,
        location="create_report",
        name="user",
        new_name="person",
    ),
    callback(
        "set_renaming",
        module_name=REPORTS,
        location="create_report",
        name="report",
        new_name="person",
    ),
    callback(
        "set_rename_to",
        module_name=REPORTS,
        location="create_summary",
        new_name="format_report",
    ),
]

# The follow-up RFA resolves the clashes. Renaming text to body turns
# title -> text into a chain, which is allowed.
RETRY_CALLBACKS = [
    callback(
        "set_renaming",
        module_name=REPORTS,
        location="create_report",
        name="text",
        new_name="body",
    ),
    callback(
        "set_renaming",
        module_name=REPORTS,
        location="create_report",
        name="report",
        new_name="document",
    ),
    callback(
        "set_rename_to",
        module_name=REPORTS,
        location="create_summary",
        new_name="summarize_user",
    ),
]


def create_env(context: Context):
    return Env(context)


def test_propose_renamings_retries_conflicting_renamings(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-renamings. Besides the modules of the base env, myapp has
    # reports.py. The RFA of the chunk proposes renamings that clash, and the
    # follow-up RFA resolves the clashes.
    if env.step(
        env.create_session_at_propose_renamings({REPORTS: REPORTS_PY}),
        env.script_rfa(RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(RETRY_RFA_ID, *RETRY_CALLBACKS),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # After the RFA of the chunk, Groupy should have made a follow-up RFA for
    # the clashes, and then finished the chunk and the stage.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.rfa_ids() == [RFA_ID, RETRY_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(CHUNK_CALLBACKS),
            *commit_messages(RETRY_CALLBACKS),
            "propose-renamings: finish group-1/chunk-1",
            "propose-renamings: finish the stage",
        ]

    # We look at the context of the follow-up RFA.
    #
    # It should list the clashes, one line per clash, sorted.
    if env.step():
        assert env.rfa(RETRY_RFA_ID).context["renaming_conflicts"] == [
            "myapp/reports.py:@module: create_summary -> format_report clashes"
            " with the existing name format_report",
            "myapp/reports.py:create_report: report -> person and user -> person"
            " have the same new name",
            "myapp/reports.py:create_report: title -> text clashes with the"
            " existing name text",
        ]

    # We look at the node file of reports.py.
    #
    # It should have the renamings of both RFAs.
    if env.step(
        env.load_module_node(REPORTS),
    ):
        assert env.function_node("create_report").renamings == {
            "title": "text",
            "text": "body",
            "user": "person",
            "report": "document",
        }
        assert env.function_node("create_summary").rename_to == "summarize_user"


class Env(TestEnv):
    pass
