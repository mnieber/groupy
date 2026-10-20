from groupy_next_tests.groupy_next_test_env import Context, TestEnv

from groupy.sessions.utils.exceptions import DetachedHeadError


def create_env(context: Context):
    return Env(context)


def test_groupy_refuses_a_detached_head(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on groupy-1, and we check out its head commit as a
    # detached HEAD (e.g. to look around).
    if env.step(
        env.create_session(grouping_strategy="simple"),
        env.install_fake_stage(),
        env.run_git("checkout", "--detach"),
        env.remember_git_head(),
    ):
        assert env.git_branch() == "HEAD"

    # We run groupy next and groupy status.
    #
    # They need the name of the current branch (e.g. for the per-branch
    # files), so they should raise a DetachedHeadError, and change nothing.
    if env.step(
        env.run_groupy_and_catch_error("next"),
    ):
        assert isinstance(env.error, DetachedHeadError)
        assert env.rfa_ids() == []
        assert env.git_head() == env.remembered_git_head

    if env.step(
        env.run_groupy_and_catch_error("status"),
    ):
        assert isinstance(env.error, DetachedHeadError)

    # We run groupy next again, as the developer does.
    #
    # Groupy should print the error, with a hint to check out a groupy branch.
    if env.step(
        env.run_groupy_cli("next"),
    ):
        assert env.exit_code == 1
        assert env.output_contains("DetachedHeadError", "groupy switch")
        assert "Traceback" not in env.output


class Env(TestEnv):
    pass
