from breaker.sessions.utils.exceptions import NoSessionError
from breaker_next_tests.breaker_next_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_breaker_next_requires_a_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, but we don't run breaker init.
    if env.step(
        env.create_repo_with_target_code(),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # It should raise a NoSessionError and leave the repo untouched.
    if env.step(
        env.run_breaker_and_catch_error("next"),
    ):
        assert isinstance(env.error, NoSessionError)
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""


class Env(TestEnv):
    pass
