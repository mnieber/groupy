from apply_renamings_tests.apply_renamings_test_env import Context, TestEnv
from groupy_next_tests.fake_policies import FakeRefactoringError

from groupy.renamings.actions.set_renaming import set_renaming

HEADINGS = "myapp/headings.py"
STATS = "myapp/stats.py"

HEADINGS_PY = """\
def format_heading(title, text):
    body = text.strip()
    return title + ": " + body
"""

RENAMED_HEADINGS_PY = """\
def format_heading(title, text):
    content = text.strip()
    return title + ": " + content
"""

STATS_PY = """\
MAX_OUTLIERS = 10


def is_outlier_point(point, limit):
    return abs(point) > limit
"""

RENAMED_STATS_PY = """\
MAX_NR_OF_OUTLIERS = 10


def is_outlier_point(point, threshold):
    return abs(point) > threshold
"""


def create_env(context: Context):
    return Env(context)


def test_apply_renamings_resumes_after_a_failed_rename(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-renamings. Besides the modules of the base env, myapp has
    # headings.py and stats.py (in this order, in the same chunk), and both
    # have renamings. The rename of limit in stats.py fails.
    if env.step(
        env.create_session_at_apply_renamings({HEADINGS: HEADINGS_PY, STATS: STATS_PY}),
        env.edit_node_file(set_renaming, HEADINGS, "format_heading", "body", "content"),
        env.edit_node_file(
            set_renaming, STATS, "@module", "MAX_OUTLIERS", "MAX_NR_OF_OUTLIERS"
        ),
        env.edit_node_file(
            set_renaming, STATS, "is_outlier_point", "limit", "threshold"
        ),
        env.commit_all("review the renamings"),
        env.fail_refactoring(STATS, "limit"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # The failed rename should interrupt the stage. The renamings of
    # headings.py should have been committed. Groupy should have discarded
    # the uncommitted changes of stats.py, so that the working tree is clean
    # and stats.py still has all its renamings.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, FakeRefactoringError)
        assert env.commit_messages_since_remembered_head() == [
            "apply-renamings: apply the renamings of myapp/headings.py",
        ]
        assert env.git_status() == ""
        assert env.read_module(HEADINGS) == RENAMED_HEADINGS_PY
        assert env.read_module(STATS) == STATS_PY
        assert env.session.next_stage == "apply-renamings"
        assert env.session.finished_chunks == []

    # The rename no longer fails, and we run groupy next again.
    #
    # Groupy should only rename the symbols of stats.py (headings.py has no
    # renamings left), and then finish the chunk and the stage.
    if env.step(
        env.clear_failing_refactorings(),
        env.clear_refactoring_calls(),
        env.remember_git_head(),
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert {module_name for module_name, _ in env.renamed_names()} == {STATS}
        assert env.commit_messages_since_remembered_head() == [
            "apply-renamings: apply the renamings of myapp/stats.py",
            "apply-renamings: finish group-1/chunk-1",
            "apply-renamings: finish the stage",
        ]
        assert env.read_module(HEADINGS) == RENAMED_HEADINGS_PY
        assert env.read_module(STATS) == RENAMED_STATS_PY
        assert env.session.next_stage == "extract-methods"


class Env(TestEnv):
    pass
