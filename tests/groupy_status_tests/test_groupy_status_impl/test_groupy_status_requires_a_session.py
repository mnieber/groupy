from groupy_status_tests.groupy_status_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_status_requires_a_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the target code, but no session.
    if env.step(
        env.create_repo_with_target_code(),
    ):
        pass

    # We run groupy status.
    #
    # It should print the NoSessionError, with a hint to run groupy init, and
    # exit with code 1.
    if env.step(
        env.run_groupy_cli("status"),
    ):
        assert env.exit_code == 1
        assert env.output_contains("NoSessionError", "groupy init")


class Env(TestEnv):
    pass
