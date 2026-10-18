from groupy_status_tests.groupy_status_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_status_reports_a_finished_refactoring(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, in which all stages have run.
    if env.step(
        env.create_session(grouping_strategy="simple"),
        env.set_next_stage("done"),
    ):
        pass

    # We run groupy status.
    #
    # It should print that the refactoring is done.
    if env.step(
        env.run_groupy_cli("status"),
    ):
        assert env.exit_code == 0
        assert env.output_contains("refactoring is done")
        assert "will start" not in env.output
        assert "will resume" not in env.output


class Env(TestEnv):
    pass
