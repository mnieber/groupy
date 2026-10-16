from breaker.sessions.utils.exceptions import NoGroupFileError
from breaker_next_tests.breaker_next_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_breaker_next_requires_a_group_file(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, and the first stage is replaced
    # by a fake stage. We delete the group file and commit the deletion.
    if env.step(
        env.create_session(grouping_strategy="simple"),
        env.install_fake_stage(),
        env.run_git("rm", ".breaker/groups.txt"),
        env.commit_all("delete the group file"),
        env.remember_git_head(),
    ):
        assert env.git_status() == ""

    # We run breaker next.
    #
    # It should raise a NoGroupFileError before it runs the stage.
    if env.step(
        env.run_breaker_and_catch_error("next"),
        env.load_session(),
    ):
        assert isinstance(env.error, NoGroupFileError)
        assert env.git_head() == env.remembered_git_head
        assert env.rfa_ids() == []
        assert env.session.next_stage == "identify-helper-functions"


class Env(TestEnv):
    pass
