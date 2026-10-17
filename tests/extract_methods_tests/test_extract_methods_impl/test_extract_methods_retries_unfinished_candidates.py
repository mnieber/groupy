from breaker.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)
from breaker_next_tests.breaker_next_test_env import callback
from extract_methods_tests.extract_methods_test_env import (
    Context,
    TestEnv,
    commit_messages,
)

TITLES = "myapp/titles.py"

RFA_ID = "extract-methods/group-1/chunk-1"
RETRY_RFA_ID = "extract-methods/group-1/chunk-1/retry-1"
RFR_ID = "extract_method/myapp/titles.py:format_title/capitalize_words"

TITLES_PY = """\
def format_title(text):
    words = text.split()
    words = [word.capitalize() for word in words]
    return " ".join(words)


def clean_text(text):
    text = text.strip()
    return text.replace("  ", " ")


def count_words(text):
    return len(text.split())
"""

# The text of titles.py that the RFR writes.
EXTRACTED_TITLES_PY = """\
def format_title(text):
    return " ".join(capitalize_words(text.split()))


def capitalize_words(words):
    return [word.capitalize() for word in words]


def clean_text(text):
    text = text.strip()
    return text.replace("  ", " ")


def count_words(text):
    return len(text.split())
"""

# The RFA of the chunk extracts capitalize_words from format_title (without
# nesting it), and forgets clean_text.
CHUNK_CALLBACKS = [
    callback(
        "extract_method",
        module_name=TITLES,
        location="format_title",
        new_name="capitalize_words",
        description="Capitalize the words",
    ),
    callback(
        "set_extract_method_priority",
        module_name=TITLES,
        location="capitalize_words",
        priority="n/a",
    ),
    callback(
        "set_extract_method_priority",
        module_name=TITLES,
        location="format_title",
        priority="n/a",
    ),
]

# The follow-up RFA decides not to extract anything from clean_text.
RETRY_CALLBACKS = [
    callback(
        "set_extract_method_priority",
        module_name=TITLES,
        location="clean_text",
        priority="n/a",
    ),
]


def create_env(context: Context):
    return Env(context)


def test_extract_methods_retries_unfinished_candidates(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # extract-methods. Besides the modules of the base env, myapp has
    # titles.py, where format_title has a high priority, clean_text a medium
    # priority, and count_words the priority n/a. All modules are in one
    # chunk.
    if env.step(
        env.create_session_at_extract_methods({TITLES: TITLES_PY}),
        env.edit_node_file(set_extract_method_priority, TITLES, "format_title", "high"),
        env.edit_node_file(set_extract_method_priority, TITLES, "clean_text", "medium"),
        env.edit_node_file(set_extract_method_priority, TITLES, "count_words", "n/a"),
        env.commit_all("analyze the terminology"),
        env.script_rfa(RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(RETRY_RFA_ID, *RETRY_CALLBACKS),
        env.script_rfr(RFR_ID, {TITLES: EXTRACTED_TITLES_PY}),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # After the RFA of the chunk, Breaker should have made a follow-up RFA for
    # clean_text, and then finished the chunk and the stage. No helper was
    # nested, so there is no rename_helper_functions commit.
    if env.step(
        env.run_breaker("next"),
    ):
        assert env.rfa_ids() == [RFA_ID, RETRY_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(CHUNK_CALLBACKS),
            *commit_messages(RETRY_CALLBACKS),
            "extract-methods: finish group-1/chunk-1",
            "extract-methods: finish the stage",
        ]

    # We look at the context of the RFAs.
    #
    # The candidates should be listed with the high priority first. The
    # follow-up RFA should list the candidate that is not finished.
    if env.step():
        assert env.rfa(RFA_ID).context["extract_method_candidates"] == [
            "myapp/titles.py:format_title",
            "myapp/titles.py:clean_text",
        ]
        assert env.rfa(RETRY_RFA_ID).context["unfinished_candidates"] == [
            "myapp/titles.py:clean_text"
        ]

    # We look at titles.py and its node file.
    #
    # The extracted function was not nested, so it should keep its name, and
    # its node should be a top-level function node, in source order.
    if env.step(
        env.load_module_node(TITLES),
    ):
        assert env.read_module(TITLES) == EXTRACTED_TITLES_PY
        assert env.names(env.module_node.function_nodes) == [
            "format_title",
            "capitalize_words",
            "clean_text",
            "count_words",
        ]


class Env(TestEnv):
    pass
