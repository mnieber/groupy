from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_from_a_stage_refuses_a_target_dir(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1.
    if env.step(
        env.create_session_with_two_chunks(),
        env.remember_git_head(),
    ):
        pass

    # We run groupy init --from-stage=group-modules --target-dir=src.
    #
    # The target dir is in the session file, so it should exit with the usage
    # error of --target-dir, and leave the repo untouched.
    if env.step(
        env.run_groupy_and_catch_exit(
            "init", "--accept-risks", "--from-stage=group-modules", "--target-dir=src"
        ),
    ):
        assert env.system_exit.code == 2
        assert env.output_contains("--target-dir")
        assert env.git_branch() == "groupy-1"
        assert env.git_head() == env.remembered_git_head
        assert not env.file_exists(".groupy/groupy-2")

    # We run groupy init without --from-stage and without --target-dir.
    #
    # Then --target-dir is required, so it should exit with its usage error.
    if env.step(
        env.run_groupy_and_catch_exit("init", "--accept-risks"),
    ):
        assert env.system_exit.code == 2
        assert env.output_contains("--target-dir")
        assert env.git_branch() == "groupy-1"


class Env(TestEnv):
    pass
