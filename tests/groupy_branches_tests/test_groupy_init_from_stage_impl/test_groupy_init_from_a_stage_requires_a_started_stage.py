from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv

from groupy.sessions.utils.exceptions import NoGroupyBranchError, StageNotStartedError


def create_env(context: Context):
    return Env(context)


def test_groupy_init_from_a_stage_requires_a_started_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, which finished the stage
    # identify-helper-functions, and a branch feature-x without a session.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_groupy("next"),
        env.run_git("branch", "feature-x", "main"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy init --from-stage=analyze-terminology.
    #
    # analyze-terminology has not started (it has no start tag), so it should
    # raise a StageNotStartedError and leave the repo untouched.
    if env.step(
        env.run_groupy_and_catch_error(
            "init", "--accept-risks", "--from-stage=analyze-terminology"
        ),
    ):
        assert isinstance(env.error, StageNotStartedError)
        assert env.git_branch() == "groupy-1"
        assert env.git_branches() == {"main", "groupy-1", "feature-x"}
        assert env.git_head() == env.remembered_git_head
        assert not env.file_exists(".groupy/groupy-2")

    # We run groupy init --from-stage with a branch that doesn't exist, and
    # with a branch that has no session.
    #
    # Both should raise a NoGroupyBranchError.
    if env.step(
        env.run_groupy_and_catch_error(
            "init", "--accept-risks", "--from-stage=groupy-9/init"
        ),
    ):
        assert isinstance(env.error, NoGroupyBranchError)
        assert env.git_branches() == {"main", "groupy-1", "feature-x"}

    if env.step(
        env.run_groupy_and_catch_error(
            "init", "--accept-risks", "--from-stage=feature-x/init"
        ),
    ):
        assert isinstance(env.error, NoGroupyBranchError)
        assert env.git_branches() == {"main", "groupy-1", "feature-x"}

    # We go back to main, and run groupy init --from-stage without a branch.
    #
    # main is not a groupy branch, so it should raise a NoGroupyBranchError.
    if env.step(
        env.run_git("checkout", "main"),
        env.run_groupy_and_catch_error(
            "init", "--accept-risks", "--from-stage=group-modules"
        ),
    ):
        assert isinstance(env.error, NoGroupyBranchError)
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main", "groupy-1", "feature-x"}
        assert not env.file_exists(".groupy/groupy-2")


class Env(TestEnv):
    pass
