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

    # We run groupy reset --force.
    #
    # Groupy should say that there is nothing to reset, and change nothing.
    if env.step(
        env.run_groupy_reset("--force"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.output_contains(
            "There is nothing to reset: analyze-terminology has not started."
        )
        assert env.git_head() == env.remembered_git_head
        assert env.git_tags() == {
            "groupy/groupy-1/init",
            "groupy/groupy-1/group-modules/start",
            "groupy/groupy-1/identify-helper-functions/start",
        }
        assert env.session.next_stage == "analyze-terminology"

    # We run groupy reset extract-methods --force, for a later stage.
    #
    # Groupy should say that there is nothing to reset, and change nothing.
    if env.step(
        env.run_groupy_reset("extract-methods", "--force"),
    ):
        assert env.exit_code == 0
        assert env.output_contains(
            "There is nothing to reset: extract-methods has not started."
        )
        assert env.git_head() == env.remembered_git_head

    # We run groupy reset with a name that is not a stage.
    #
    # It should exit with a usage error, and change nothing.
    if env.step(
        env.run_groupy_and_catch_exit("reset", "extract-method", "--force"),
    ):
        assert env.system_exit.code == 2
        assert env.output_contains("extract-method")
        assert env.git_head() == env.remembered_git_head


class Env(TestEnv):
    pass
