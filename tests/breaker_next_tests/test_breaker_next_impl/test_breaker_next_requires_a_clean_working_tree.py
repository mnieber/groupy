from breaker.sessions.utils.exceptions import DirtyWorkingTreeError
from breaker_next_tests.breaker_next_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_breaker_next_requires_a_clean_working_tree(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, and the first stage is replaced
    # by a fake stage. We change a tracked file without committing it.
    if env.step(
        env.create_session(grouping_strategy="simple"),
        env.install_fake_stage(),
        env.append_to_file("src/myapp/books.py", "\nDEFAULT_TITLE = 'Untitled'\n"),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # It should raise a DirtyWorkingTreeError before it runs the stage.
    if env.step(
        env.run_breaker_and_catch_error("next"),
        env.load_session(),
    ):
        assert isinstance(env.error, DirtyWorkingTreeError)
        assert env.git_head() == env.remembered_git_head
        assert env.rfa_ids() == []
        assert env.session.next_stage == "identify-helper-functions"


class Env(TestEnv):
    pass
