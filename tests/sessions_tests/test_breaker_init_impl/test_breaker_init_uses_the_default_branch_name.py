from sessions_tests.breaker_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_breaker_init_uses_the_default_branch_name(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package in the src dir.
    if env.step(
        env.create_repo_with_target_code(),
    ):
        pass

    # We run breaker init without --branch-name.
    #
    # The branch name should default to "breaker".
    if env.step(
        env.run_breaker("init", "--target-dir=src"),
    ):
        assert env.git_branch() == "breaker"


class Env(TestEnv):
    pass
