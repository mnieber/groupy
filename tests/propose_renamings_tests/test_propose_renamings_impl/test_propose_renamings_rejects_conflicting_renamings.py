from groupy.renamings.actions.propose_renamings import ProposedRenamingHasConflictError
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
class Report:
    def __init__(self, title):
        self.title = title

    def save(self):
        pass

    def store(self):
        pass


def create_report(title, text):
    return Report(title + text)
"""

# The RFA of the chunk proposes a swap of title and text in create_report,
# and renames the save method of Report to the name of the store method.
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
        name="text",
        new_name="title",
    ),
    callback(
        "set_rename_to",
        module_name=REPORTS,
        location="Report.save",
        new_name="store",
    ),
]


def create_env(context: Context):
    return Env(context)


def test_propose_renamings_rejects_conflicting_renamings(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-renamings. Besides the modules of the base env, myapp has
    # reports.py. The RFA of the chunk proposes renamings that clash, and the
    # follow-up RFA does not resolve them.
    if env.step(
        env.create_session_at_propose_renamings({REPORTS: REPORTS_PY}),
        env.script_rfa(RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(RETRY_RFA_ID),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should raise an error that lists the clashes, which interrupts
    # the stage. A swap is a clash, because the renamings have no order in
    # which they can be applied. The chunk should not be finished, but the
    # callbacks should have been committed.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, ProposedRenamingHasConflictError)
        assert (
            "myapp/reports.py:Report: save -> store clashes with the existing"
            " name store" in str(env.error)
        )
        assert (
            "myapp/reports.py:create_report: text -> title and title -> text"
            " form a cycle" in str(env.error)
        )
        assert env.rfa_ids() == [RFA_ID, RETRY_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(CHUNK_CALLBACKS),
        ]
        assert env.git_status() == ""
        assert env.session.next_stage == "propose-renamings"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
