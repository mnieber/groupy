from analyze_terminology_tests.analyze_terminology_test_env import (
    CONSOLIDATION_RFA_ID,
    Context,
    TestEnv,
    commit_messages,
    priority_callbacks,
)

RFA_ID = "analyze-terminology/group-1/chunk-1"
RETRY_RFA_ID = "analyze-terminology/group-1/chunk-1/retry-1"

# The RFA of the chunk forgets Book.__init__, _normalize_title and
# create_chapter.
CHUNK_CALLBACKS = [
    *priority_callbacks("myapp/books.py", "Book", "create_book"),
    *priority_callbacks("myapp/chapters/chapter_titles.py", "number_heading"),
]

RETRY_CALLBACKS = [
    *priority_callbacks("myapp/books.py", "Book.__init__", "_normalize_title"),
    *priority_callbacks("myapp/chapters/create_chapter.py", "create_chapter"),
]


def create_env(context: Context):
    return Env(context)


def test_analyze_terminology_retries_unanalyzed_nodes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # analyze-terminology. With the simple grouping strategy, all modules are
    # in one chunk. The RFA of the chunk does not set the
    # extract_method_priority of every function and class node, and the
    # follow-up RFA sets the missing ones.
    if env.step(
        env.create_session_at_analyze_terminology(grouping_strategy="simple"),
        env.script_rfa(RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(RETRY_RFA_ID, *RETRY_CALLBACKS),
        env.script_rfa(CONSOLIDATION_RFA_ID),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # After the RFA of the chunk, Groupy should have made a follow-up RFA for
    # the nodes without an extract_method_priority, and then finished the
    # chunk and the stage.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.rfa_ids() == [RFA_ID, RETRY_RFA_ID, CONSOLIDATION_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(CHUNK_CALLBACKS),
            *commit_messages(RETRY_CALLBACKS),
            "analyze-terminology: finish group-1/chunk-1",
            "analyze-terminology: finish consolidate-glossary",
            "analyze-terminology: finish the stage",
        ]

    # We look at the context of the follow-up RFA.
    #
    # It should list the locations of the nodes that were not analyzed,
    # sorted.
    if env.step():
        assert env.rfa(RETRY_RFA_ID).context["unanalyzed_nodes"] == [
            "myapp/books.py:Book.__init__",
            "myapp/books.py:_normalize_title",
            "myapp/chapters/create_chapter.py:create_chapter",
        ]


class Env(TestEnv):
    pass
