from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_switch_and_leave_move_between_sessions(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, which finished the stage
    # identify-helper-functions. Then we start a second session with groupy
    # init, on branch groupy-2.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_groupy("next"),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.load_session(),
    ):
        assert env.git_branch() == "groupy-2"
        assert env.session.next_stage == "group-modules"

    # We run groupy switch groupy-1.
    #
    # The working tree is clean, so Groupy should switch without asking, and
    # say what the next stage of groupy-1 is.
    if env.step(
        env.run_groupy_command("switch", "groupy-1"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.prompts == []
        assert env.output_contains(
            "Switched to groupy-1 (next stage: analyze-terminology)."
        )
        assert env.git_branch() == "groupy-1"
        assert env.session.next_stage == "analyze-terminology"

    # We run groupy leave.
    #
    # Groupy should go back to the base branch, and keep groupy-1.
    if env.step(
        env.run_groupy_command("leave"),
    ):
        assert env.exit_code == 0
        assert env.prompts == []
        assert env.output_contains("Left groupy-1; it is kept. Back on main.")
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main", "groupy-1", "groupy-2"}
        assert not env.file_exists(".groupy/session.yaml")

    # We run groupy switch groupy-2, from the base branch.
    #
    # Groupy should switch to groupy-2.
    if env.step(
        env.run_groupy_command("switch", "groupy-2"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.output_contains("Switched to groupy-2 (next stage: group-modules).")
        assert env.git_branch() == "groupy-2"
        assert env.session.next_stage == "group-modules"


class Env(TestEnv):
    pass
