from groupy.sessions.utils.exceptions import NoSessionError
from groupy_sync_tests.groupy_sync_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_sync_requires_a_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, but we don't run groupy init.
    if env.step(
        env.create_repo_with_target_code(),
    ):
        pass

    # We run groupy sync.
    #
    # Groupy needs the session to find the target code, so it should raise a
    # NoSessionError.
    if env.step(
        env.run_groupy_and_catch_error("sync"),
    ):
        assert isinstance(env.error, NoSessionError)


class Env(TestEnv):
    pass
