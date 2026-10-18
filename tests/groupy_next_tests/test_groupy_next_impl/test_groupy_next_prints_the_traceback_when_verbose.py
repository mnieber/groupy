from groupy_next_tests.groupy_next_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_next_prints_the_traceback_when_verbose(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, and the first stage is replaced
    # by a fake stage. The RFA of the only chunk has no script.
    if env.step(
        env.create_session(
            grouping_strategy="simple", max_group_lines=10000, max_chunk_lines=10000
        ),
        env.install_fake_stage(),
    ):
        pass

    # We run groupy -v next.
    #
    # The stage should be interrupted, and Groupy should print the traceback
    # as well as the error.
    if env.step(
        env.run_groupy_cli("-v", "next"),
    ):
        assert env.exit_code == 1
        assert env.output_contains(
            "Traceback",
            "UnscriptedRequestError",
            "identify-helper-functions/group-1/chunk-1",
        )


class Env(TestEnv):
    pass
