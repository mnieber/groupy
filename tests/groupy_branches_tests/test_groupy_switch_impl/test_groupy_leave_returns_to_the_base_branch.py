from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_leave_returns_to_the_base_branch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package and a branch develop. We start
    # a session from develop.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_git("branch", "develop"),
        env.run_groupy("init", "--accept-risks", "--target-dir=src", "--base=develop"),
    ):
        assert env.git_branch() == "groupy-1"

    # We add an untracked file, run groupy leave, and answer yes.
    #
    # Groupy should list the untracked file, ask for confirmation, discard the
    # file, and go back to develop (the base branch of the session).
    if env.step(
        env.write_file("notes.txt", "Some notes.\n"),
        env.run_groupy_command("leave", answer="y"),
    ):
        assert env.exit_code == 0
        assert len(env.prompts) == 1
        assert env.output_contains("these uncommitted changes:", "notes.txt")
        assert env.output_contains("Left groupy-1; it is kept. Back on develop.")
        assert env.git_branch() == "develop"
        assert env.git_status() == ""

    # We switch back to groupy-1, change the README, and run groupy leave
    # --force.
    #
    # Groupy should discard the change and leave, without asking.
    if env.step(
        env.run_groupy_command("switch", "groupy-1"),
        env.append_to_file("README.md", "Work in progress.\n"),
        env.run_groupy_command("leave", "--force"),
    ):
        assert env.exit_code == 0
        assert env.prompts == []
        assert env.git_branch() == "develop"
        assert env.git_status() == ""


class Env(TestEnv):
    pass
