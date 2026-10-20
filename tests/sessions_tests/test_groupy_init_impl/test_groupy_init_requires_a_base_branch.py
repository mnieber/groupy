from sessions_tests.groupy_test_env import Context, TestEnv

from groupy.sessions.actions.init_session import NoBaseBranchError


def create_env(context: Context):
    return Env(context)


def test_groupy_init_requires_a_base_branch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, where the main branch is
    # called master.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_git("branch", "-M", "master"),
        env.remember_git_head(),
    ):
        assert env.git_branches() == {"master"}

    # We run groupy init without --base.
    #
    # The default base branch main doesn't exist, so it should raise a
    # NoBaseBranchError and leave the repo untouched.
    if env.step(
        env.run_groupy_and_catch_error("init", "--accept-risks", "--target-dir=src"),
    ):
        assert isinstance(env.error, NoBaseBranchError)
        assert env.git_branch() == "master"
        assert env.git_branches() == {"master"}
        assert env.git_head() == env.remembered_git_head
        assert not env.file_exists(".groupy")

    # We run groupy init again, as the developer does.
    #
    # Groupy should print the error, with a hint to use --base.
    if env.step(
        env.run_groupy_cli("init", "--accept-risks", "--target-dir=src"),
    ):
        assert env.exit_code == 1
        assert env.output_contains("NoBaseBranchError", "--base")
        assert "Traceback" not in env.output

    # We run groupy init with --base=master.
    #
    # It should create the branch groupy-1 from master, and record master as
    # the base branch.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src", "--base=master"),
        env.load_session(),
    ):
        assert env.git_branch() == "groupy-1"
        assert env.commit_of("groupy-1~1") == env.remembered_git_head
        assert env.session.base_branch == "master"


class Env(TestEnv):
    pass
