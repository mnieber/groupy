from sessions_tests.groupy_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_uses_the_default_branch_name(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package in the src dir.
    if env.step(
        env.create_repo_with_target_code(),
    ):
        pass

    # We run groupy init without --branch-name.
    #
    # The branch name should default to "groupy".
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        assert env.git_branch() == "groupy"


class Env(TestEnv):
    pass
