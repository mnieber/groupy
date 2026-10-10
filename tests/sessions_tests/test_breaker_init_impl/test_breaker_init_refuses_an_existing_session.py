from breaker.sessions.actions.init_session import SessionExistsError
from sessions_tests.breaker_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_breaker_init_refuses_an_existing_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, and we run breaker init.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_breaker("init", "--target-dir=src"),
        env.remember_git_head(),
    ):
        assert env.file_exists(".breaker/session.yaml")

    # We run breaker init again, with another branch name.
    #
    # The working tree is clean, but there already is a session file, so it
    # should raise a SessionExistsError and leave the repo untouched.
    if env.step(
        env.run_breaker_and_catch_error(
            "init", "--target-dir=src", "--branch-name=breaker-2"
        ),
    ):
        assert isinstance(env.error, SessionExistsError)
        assert env.git_branch() == "breaker"
        assert env.git_branches() == {"main", "breaker"}
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""


class Env(TestEnv):
    pass
