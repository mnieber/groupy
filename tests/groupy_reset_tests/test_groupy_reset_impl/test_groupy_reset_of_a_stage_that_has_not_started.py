from groupy_reset_tests.groupy_reset_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_reset_of_a_stage_that_has_not_started(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session with two chunks, in which the first stage has finished,
    # so that the next stage (analyze-terminology) has not started.
    if env.step(
        env.create_session_with_two_chunks(),
        env.script_first_chunk(),
        env.script_second_chunk(),
        env.run_groupy("next"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy reset --yes.
    #
    # Groupy should say that there is nothing to reset, and change nothing.
    if env.step(
        env.run_groupy_reset("--yes"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.output_contains("nothing to reset")
        assert env.git_head() == env.remembered_git_head
        assert env.git_tags() == {
            "groupy/init",
            "groupy/identify-helper-functions/start",
        }
        assert env.session.next_stage == "analyze-terminology"


class Env(TestEnv):
    pass
