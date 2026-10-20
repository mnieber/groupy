from groupy_status_tests.groupy_status_test_env import Context, TestEnv

RFA_ID = "identify-helper-functions/group-1/chunk-1"


def create_env(context: Context):
    return Env(context)


def test_groupy_status_all_reports_every_branch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on groupy-1, which finished group-modules. Claude cost
    # 0.10 USD on it.
    if env.step(
        env.create_session(grouping_strategy="simple"),
        env.write_claude_log(RFA_ID, 0.10),
    ):
        assert env.git_branch() == "groupy-1"

    # We start a session on groupy-2, which has not run yet. Its log has a
    # session of 0.05 USD and an aborted session (whose cost is unknown).
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.write_claude_log(RFA_ID, 0.05, is_aborted=True),
    ):
        assert env.git_branch() == "groupy-2"

    # We start a session on groupy-3, where Claude cost 0.20 USD, and abort it.
    # Then we are back on main.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.write_claude_log(RFA_ID, 0.20),
        env.run_groupy_cli("abort", "--force"),
    ):
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main", "groupy-1", "groupy-2"}

    # We run groupy status --all on main.
    #
    # It should print a line per groupy branch, with its next stage, its last
    # run and its costs, and a line for the aborted branch with its costs. No
    # branch is the current one. The total is a lower bound, since the costs
    # of groupy-2 are.
    if env.step(
        env.run_groupy_cli("status", "--all"),
    ):
        assert env.exit_code == 0
        assert env.output_line("groupy-1") == (
            "  groupy-1: next stage identify-helper-functions, last run finished, "
            "costs 0.10 USD"
        )
        assert env.output_line("groupy-2") == (
            "  groupy-2: next stage group-modules, no run yet, "
            "costs at least 0.05 USD"
        )
        assert env.output_line("groupy-3") == "  groupy-3 (aborted): costs 0.20 USD"
        assert env.output_line("Total costs") == "Total costs: at least 0.35 USD"

    # We switch to groupy-2, and run groupy status --all again.
    #
    # The line of groupy-2 should be marked as the current branch.
    if env.step(
        env.run_groupy_cli("switch", "groupy-2"),
        env.run_groupy_cli("status", "--all"),
    ):
        assert env.exit_code == 0
        assert env.output_line("groupy-2").startswith("* groupy-2:")
        assert env.output_line("groupy-1").startswith("  groupy-1:")


class Env(TestEnv):
    pass
