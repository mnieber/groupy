from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv

from groupy.sessions.utils.exceptions import NoSessionError


def create_env(context: Context):
    return Env(context)


def test_groupy_leave_requires_a_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, and we go back to main.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_git("checkout", "main"),
    ):
        pass

    # We run groupy leave on main.
    #
    # There is no session on main, so it should raise a NoSessionError.
    if env.step(
        env.run_groupy_and_catch_error("leave"),
    ):
        assert isinstance(env.error, NoSessionError)
        assert env.git_branch() == "main"

    # We run groupy leave again, as the developer does.
    #
    # Groupy should print the error, with a hint to switch to a session or to
    # start one.
    if env.step(
        env.run_groupy_command("leave"),
    ):
        assert env.exit_code == 1
        assert env.output_contains(
            "NoSessionError", "groupy switch <branch_name>", "groupy init"
        )
        assert "Traceback" not in env.output


class Env(TestEnv):
    pass
