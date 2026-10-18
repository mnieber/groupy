from analyze_terminology_tests.analyze_terminology_test_env import (
    Context,
    TestEnv,
    commit_messages,
    priority_callbacks,
)

from groupy.concepts.actions.analyze_terminology import UnanalyzedNodesError

RFA_ID = "analyze-terminology/group-1/chunk-1"
RETRY_RFA_ID = "analyze-terminology/group-1/chunk-1/retry-1"

# The RFA of the chunk forgets Book.__init__, _normalize_title and
# create_chapter.
CHUNK_CALLBACKS = [
    *priority_callbacks("myapp/books.py", "Book", "create_book"),
    *priority_callbacks("myapp/chapters/chapter_titles.py", "number_heading"),
]

# The follow-up RFA still forgets create_chapter.
RETRY_CALLBACKS = [
    *priority_callbacks("myapp/books.py", "Book.__init__", "_normalize_title"),
]


def create_env(context: Context):
    return Env(context)


def test_analyze_terminology_rejects_unanalyzed_nodes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # analyze-terminology. With the simple grouping strategy, all modules are
    # in one chunk. Neither the RFA of the chunk nor the follow-up RFA sets
    # the extract_method_priority of create_chapter.
    if env.step(
        env.create_session_at_analyze_terminology(grouping_strategy="simple"),
        env.script_rfa(RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(RETRY_RFA_ID, *RETRY_CALLBACKS),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should raise an error that names the node that is still not
    # analyzed, which interrupts the stage. The chunk should not be finished,
    # but the callbacks should have been committed.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, UnanalyzedNodesError)
        assert "myapp/chapters/create_chapter.py:create_chapter" in str(env.error)
        assert env.rfa_ids() == [RFA_ID, RETRY_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(CHUNK_CALLBACKS),
            *commit_messages(RETRY_CALLBACKS),
        ]
        assert env.git_status() == ""
        assert env.session.next_stage == "analyze-terminology"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
