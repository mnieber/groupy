from breaker_next_tests.breaker_next_test_env import (
    Context,
    TestEnv,
    callback,
)
from breaker_next_tests.fake_policies import UnscriptedRequestError


def create_env(context: Context):
    return Env(context)


def test_breaker_next_resumes_an_interrupted_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, with the package grouping
    # strategy, so that the modules of myapp (group 1) and of myapp/chapters
    # (group 2) are in different chunks. The first stage is replaced by a fake
    # stage that makes an RFA per chunk. Only the RFA of the first chunk has a
    # script.
    if env.step(
        env.create_session(
            grouping_strategy="package", max_group_lines=10000, max_chunk_lines=10000
        ),
        env.install_fake_stage(),
        env.script_rfa(
            "identify-helper-functions/group-1/chunk-1",
            callback(
                "add_responsibility",
                module_name="myapp/books.py",
                location="create_book",
                responsibility="Creates a book",
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # The RFA of the second chunk has no script, so the fake policy should
    # raise an error, which interrupts the stage. The first chunk should have
    # been committed and recorded as finished.
    if env.step(
        env.run_breaker_and_catch_error("next"),
        env.load_session(),
    ):
        assert isinstance(env.error, UnscriptedRequestError)
        assert env.commit_messages_since_remembered_head() == [
            "identify-helper-functions: add_responsibility",
            "identify-helper-functions: finish group-1/chunk-1",
        ]
        assert env.git_status() == ""
        assert env.session.next_stage == "identify-helper-functions"
        assert env.session.finished_chunks == [
            "identify-helper-functions/group-1/chunk-1"
        ]

    # We add a script for the second chunk, and run breaker next again.
    #
    # It should resume the stage at the second chunk, and then finish the
    # stage.
    if env.step(
        env.script_rfa(
            "identify-helper-functions/group-2/chunk-1",
            callback(
                "add_responsibility",
                module_name="myapp/chapters/create_chapter.py",
                location="create_chapter",
                responsibility="Creates a chapter",
            ),
        ),
        env.clear_rfa_requests(),
        env.remember_git_head(),
        env.run_breaker("next"),
    ):
        assert env.rfa_ids() == ["identify-helper-functions/group-2/chunk-1"]
        assert env.commit_messages_since_remembered_head() == [
            "identify-helper-functions: add_responsibility",
            "identify-helper-functions: finish group-2/chunk-1",
            "identify-helper-functions: finish the stage",
        ]

    # We look at the node files and the session.
    #
    # The first chunk should not have been processed twice, and the stage
    # should be finished.
    if env.step(
        env.load_session(),
    ):
        assert env.responsibilities("myapp/books.py", "create_book") == [
            "Creates a book"
        ]
        assert env.responsibilities(
            "myapp/chapters/create_chapter.py", "create_chapter"
        ) == ["Creates a chapter"]
        assert env.session.next_stage == "analyze-terminology"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
