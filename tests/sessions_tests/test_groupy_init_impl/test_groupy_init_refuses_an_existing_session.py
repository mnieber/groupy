from sessions_tests.groupy_test_env import Context, TestEnv

from groupy.sessions.actions.init_session import SessionExistsError


def create_env(context: Context):
    return Env(context)


def test_groupy_init_refuses_an_existing_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, and we run groupy init.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.remember_git_head(),
    ):
        assert env.file_exists(".groupy/session.yaml")

    # We run groupy init again, with another branch name.
    #
    # The working tree is clean, but there already is a session file, so it
    # should raise a SessionExistsError and leave the repo untouched.
    if env.step(
        env.run_groupy_and_catch_error(
            "init", "--accept-risks", "--target-dir=src", "--branch-name=groupy-2"
        ),
    ):
        assert isinstance(env.error, SessionExistsError)
        assert env.git_branch() == "groupy"
        assert env.git_branches() == {"main", "groupy"}
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""


class Env(TestEnv):
    pass
