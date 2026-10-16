from breaker.sessions.utils.exceptions import NoSessionError
from breaker_sync_tests.breaker_sync_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_breaker_sync_requires_a_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, but we don't run breaker init.
    if env.step(
        env.create_repo_with_target_code(),
    ):
        pass

    # We run breaker sync.
    #
    # Breaker needs the session to find the target code, so it should raise a
    # NoSessionError.
    if env.step(
        env.run_breaker_and_catch_error("sync"),
    ):
        assert isinstance(env.error, NoSessionError)


class Env(TestEnv):
    pass
