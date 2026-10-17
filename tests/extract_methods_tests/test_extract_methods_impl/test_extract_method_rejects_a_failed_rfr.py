from breaker.functions.actions.extract_method import ExtractMethodFailedError
from breaker.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)
from breaker_next_tests.breaker_next_test_env import callback, file_write
from extract_methods_tests.extract_methods_test_env import Context, TestEnv

TITLES = "myapp/titles.py"

RFA_ID = "extract-methods/group-1/chunk-1"
RFR_ID = "extract_method/myapp/titles.py:format_title/capitalize_words"

TITLES_PY = """\
def format_title(text):
    words = text.split()
    words = [word.capitalize() for word in words]
    return " ".join(words)
"""

# The text of titles.py that the RFR writes. It changes format_title, but
# does not add capitalize_words.
FAILED_TITLES_PY = """\
def format_title(text):
    return " ".join(word.capitalize() for word in text.split())
"""


def create_env(context: Context):
    return Env(context)


def test_extract_method_rejects_a_failed_rfr(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # extract-methods. Besides the modules of the base env, myapp has
    # titles.py, where format_title has a high priority. All modules are in
    # one chunk. The RFA of the chunk extracts capitalize_words, but the RFR
    # does not add this function.
    if env.step(
        env.create_session_at_extract_methods({TITLES: TITLES_PY}),
        env.edit_node_file(set_extract_method_priority, TITLES, "format_title", "high"),
        env.commit_all("analyze the terminology"),
        env.script_rfa(
            RFA_ID,
            callback(
                "extract_method",
                module_name=TITLES,
                location="format_title",
                new_name="capitalize_words",
                description="Capitalize the words",
            ),
        ),
        env.script_rfr(RFR_ID, file_write(TITLES, FAILED_TITLES_PY)),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # Breaker should raise an error that names the missing function, which
    # interrupts the stage. It should have discarded the changes of the RFR,
    # and not committed anything.
    if env.step(
        env.catch_error(env.run_breaker, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, ExtractMethodFailedError)
        assert "capitalize_words" in str(env.error)
        assert env.commit_messages_since_remembered_head() == []
        assert env.git_status() == ""
        assert env.read_module(TITLES) == TITLES_PY
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
