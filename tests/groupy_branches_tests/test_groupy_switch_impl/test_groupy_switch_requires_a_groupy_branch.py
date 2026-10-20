from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv

from groupy.sessions.utils.exceptions import NoGroupyBranchError


def create_env(context: Context):
    return Env(context)


def test_groupy_switch_requires_a_groupy_branch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, and a branch feature-x without a
    # session.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_git("branch", "feature-x", "main"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy switch with a branch that doesn't exist, with a branch
    # without a session, and with the base branch.
    #
    # Each should raise a NoGroupyBranchError, and change nothing.
    if env.step(
        env.run_groupy_and_catch_error("switch", "groupy-9"),
    ):
        assert isinstance(env.error, NoGroupyBranchError)
        assert env.git_branch() == "groupy-1"

    if env.step(
        env.run_groupy_and_catch_error("switch", "feature-x"),
    ):
        assert isinstance(env.error, NoGroupyBranchError)
        assert env.git_branch() == "groupy-1"

    if env.step(
        env.run_groupy_and_catch_error("switch", "main"),
    ):
        assert isinstance(env.error, NoGroupyBranchError)
        assert env.git_branch() == "groupy-1"
        assert env.git_head() == env.remembered_git_head

    # We run groupy switch groupy-1, while we are on groupy-1.
    #
    # Groupy should say that we are already on groupy-1, and change nothing.
    if env.step(
        env.run_groupy_command("switch", "groupy-1"),
    ):
        assert env.exit_code == 0
        assert env.output_contains("Already on groupy-1.")
        assert env.git_branch() == "groupy-1"
        assert env.git_head() == env.remembered_git_head


class Env(TestEnv):
    pass
