from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv

from groupy.sessions.utils.exceptions import NoGroupyBranchError, NoSessionError


def create_env(context: Context):
    return Env(context)


def test_groupy_abort_requires_a_groupy_branch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, and a branch feature-x without a
    # session. We go back to main.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_git("branch", "feature-x", "main"),
        env.run_git("checkout", "main"),
    ):
        pass

    # We run groupy abort on main, without a branch name.
    #
    # There is no session on main, so it should raise a NoSessionError.
    if env.step(
        env.run_groupy_and_catch_error("abort", "--force"),
    ):
        assert isinstance(env.error, NoSessionError)
        assert env.git_branches() == {"main", "groupy-1", "feature-x"}

    # We run groupy abort with a branch that doesn't exist, with a branch
    # without a session, and with the base branch.
    #
    # Each should raise a NoGroupyBranchError, and delete nothing.
    if env.step(
        env.run_groupy_and_catch_error("abort", "groupy-9", "--force"),
    ):
        assert isinstance(env.error, NoGroupyBranchError)

    if env.step(
        env.run_groupy_and_catch_error("abort", "feature-x", "--force"),
    ):
        assert isinstance(env.error, NoGroupyBranchError)
        assert env.git_branches() == {"main", "groupy-1", "feature-x"}

    if env.step(
        env.run_groupy_and_catch_error("abort", "main", "--force"),
    ):
        assert isinstance(env.error, NoGroupyBranchError)
        assert env.git_branches() == {"main", "groupy-1", "feature-x"}
        assert env.branch_tags("groupy-1") != set()


class Env(TestEnv):
    pass
