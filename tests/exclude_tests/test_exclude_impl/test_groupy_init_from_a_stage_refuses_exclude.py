from exclude_tests.exclude_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_from_a_stage_refuses_exclude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1 that excludes the reports package,
    # and we have run its first stage.
    if env.step(
        env.create_repo_with_reports(),
        env.run_groupy(
            "init", "--accept-risks", "--target-dir=src", "--exclude=myapp/reports/**"
        ),
        env.run_groupy("next"),
        env.remember_git_head(),
    ):
        assert env.git_branch() == "groupy-1"

    # We run groupy init --from-stage=group-modules --exclude=myapp/books.py.
    #
    # The new branch keeps the exclude patterns of the session that it starts
    # from, so it should exit with a usage error of --exclude, and leave the
    # repo untouched.
    if env.step(
        env.run_groupy_and_catch_exit(
            "init",
            "--accept-risks",
            "--from-stage=group-modules",
            "--exclude=myapp/books.py",
        ),
    ):
        assert env.system_exit.code == 2
        assert env.output_contains("--exclude")
        assert env.git_branch() == "groupy-1"
        assert env.git_head() == env.remembered_git_head
        assert not env.file_exists(".groupy/groupy-2")


class Env(TestEnv):
    pass
