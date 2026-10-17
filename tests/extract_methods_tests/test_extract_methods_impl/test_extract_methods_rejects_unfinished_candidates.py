from groupy.functions.actions.extract_methods import UnfinishedCandidatesError
from groupy.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)
from extract_methods_tests.extract_methods_test_env import Context, TestEnv

TITLES = "myapp/titles.py"

RFA_ID = "extract-methods/group-1/chunk-1"
RETRY_RFA_ID = "extract-methods/group-1/chunk-1/retry-1"

TITLES_PY = """\
def clean_text(text):
    text = text.strip()
    return text.replace("  ", " ")
"""


def create_env(context: Context):
    return Env(context)


def test_extract_methods_rejects_unfinished_candidates(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # extract-methods. Besides the modules of the base env, myapp has
    # titles.py, where clean_text has a medium priority. All modules are in
    # one chunk. Neither the RFA of the chunk nor the follow-up RFA does
    # anything.
    if env.step(
        env.create_session_at_extract_methods({TITLES: TITLES_PY}),
        env.edit_node_file(set_extract_method_priority, TITLES, "clean_text", "medium"),
        env.commit_all("analyze the terminology"),
        env.script_rfa(RFA_ID),
        env.script_rfa(RETRY_RFA_ID),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should raise an error that names the unfinished candidate,
    # which interrupts the stage. The chunk should not be finished.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, UnfinishedCandidatesError)
        assert "myapp/titles.py:clean_text" in str(env.error)
        assert env.rfa_ids() == [RFA_ID, RETRY_RFA_ID]
        assert env.git_status() == ""
        assert env.session.next_stage == "extract-methods"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
