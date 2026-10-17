from groupy.sessions.models.session import get_session
from sessions_tests.groupy_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_get_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo, we run groupy init and we get the session twice.
    #
    # The session should be a singleton.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_groupy("init", "--target-dir=src"),
        env.load_session(),
    ):
        assert get_session() is env.session
        assert get_session() is get_session()


class Env(TestEnv):
    pass
