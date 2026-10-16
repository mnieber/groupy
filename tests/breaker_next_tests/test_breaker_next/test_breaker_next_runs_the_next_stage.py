from breaker_next_tests.breaker_next_test_env import (
    Context,
    TestEnv,
    add_responsibility_callback,
)


def create_env(context: Context):
    return Env(context)


def test_breaker_next_runs_the_next_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, with the simple grouping
    # strategy and large groups and chunks. The first stage is replaced by a
    # fake stage that makes an RFA per chunk. The RFA of the only chunk adds a
    # responsibility to create_book and to create_chapter.
    if env.step(
        env.create_session(
            grouping_strategy="simple", max_group_lines=10000, max_chunk_lines=10000
        ),
        env.install_fake_stage(),
        env.script_rfa(
            "identify-helper-functions/group-1/chunk-1",
            add_responsibility_callback(
                "myapp/books.py", "create_book", "Creates a book"
            ),
            add_responsibility_callback(
                "myapp/chapters/create_chapter.py",
                "create_chapter",
                "Creates a chapter",
            ),
        ),
        env.remember_git_head(),
        env.load_session(),
    ):
        assert env.session.next_stage == "identify-helper-functions"

    # We run breaker next.
    #
    # Breaker should have run the stage and finished it, and committed after
    # each action, after the chunk and after the stage. Every commit message
    # should start with the stage id.
    if env.step(
        env.run_breaker("next"),
    ):
        assert env.commit_messages_since_remembered_head() == [
            "identify-helper-functions: add_responsibility",
            "identify-helper-functions: add_responsibility",
            "identify-helper-functions: finish group-1/chunk-1",
            "identify-helper-functions: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the RFAs and the node files.
    #
    # The fake policy should have received the RFA of the chunk, and the
    # callbacks should have added the responsibilities.
    if env.step():
        assert env.rfa_ids() == ["identify-helper-functions/group-1/chunk-1"]
        assert env.responsibilities("myapp/books.py", "create_book") == [
            "Creates a book"
        ]
        assert env.responsibilities(
            "myapp/chapters/create_chapter.py", "create_chapter"
        ) == ["Creates a chapter"]

    # We look at the session.
    #
    # The next stage should be analyze-terminology, and there should be no
    # finished chunks.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "analyze-terminology"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
