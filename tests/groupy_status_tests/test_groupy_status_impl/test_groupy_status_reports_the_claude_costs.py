from groupy_status_tests.groupy_status_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_status_reports_the_claude_costs(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, without Claude sessions yet.
    if env.step(
        env.create_session(grouping_strategy="simple"),
    ):
        pass

    # We run groupy status.
    #
    # It should report that Claude cost nothing yet.
    if env.step(
        env.run_groupy_cli("status"),
    ):
        assert env.output_contains("0.00 USD")
        assert "at least" not in env.output

    # We add the logs of two requests, where the second one (an RFR made by a
    # callback) was run twice, and run groupy status.
    #
    # It should report the sum of the costs of all sessions.
    if env.step(
        env.write_claude_log("identify-helper-functions/group-1/chunk-1", 0.10),
        env.write_claude_log(
            "extract_method/myapp/books.py:create_book/validate_title", 0.05, 0.10
        ),
        env.run_groupy_cli("status"),
    ):
        assert env.output_contains("0.25 USD")
        assert "at least" not in env.output

    # We add an aborted session (whose cost is unknown) to the first log, and
    # run groupy status.
    #
    # It should report the known costs as a lower bound.
    if env.step(
        env.write_claude_log(
            "identify-helper-functions/group-1/chunk-1", is_aborted=True
        ),
        env.run_groupy_cli("status"),
    ):
        assert env.output_contains("at least 0.25 USD")

    # We start a second session (on groupy-2) and add a log to it, then switch
    # back to groupy-1 and run groupy status.
    #
    # The costs of groupy-2 should not count for groupy-1.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.write_claude_log("group-modules", 1.00),
        env.run_groupy_cli("switch", "groupy-1"),
        env.run_groupy_cli("status"),
    ):
        assert env.output_contains("at least 0.25 USD")
        assert "1.25" not in env.output


class Env(TestEnv):
    pass
