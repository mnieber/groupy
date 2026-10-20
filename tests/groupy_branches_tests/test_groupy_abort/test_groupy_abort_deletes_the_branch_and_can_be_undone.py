from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_abort_deletes_the_branch_and_can_be_undone(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, which finished the stage
    # identify-helper-functions. Groupy left a file in the per-branch dir.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_groupy("next"),
        env.write_file(".groupy/groupy-1/last-run.yaml", "result: finished\n"),
        env.remember_branch("groupy-1"),
    ):
        assert env.branch_tags("groupy-1") == {
            "init",
            "group-modules/start",
            "identify-helper-functions/start",
        }

    # We don't want to continue this session, so we run groupy abort, and
    # answer yes.
    #
    # Groupy should say that all commits of groupy-1 will be lost (the init
    # commit, two of group-modules and five of identify-helper-functions), and
    # ask for confirmation. Then it should delete the branch and its tags, go
    # back to the base branch, and say how to undo the abort.
    if env.step(
        env.run_groupy_command("abort", answer="y"),
    ):
        assert env.exit_code == 0
        assert len(env.prompts) == 1
        assert env.output_contains(
            "all 8 commits on branch groupy-1",
            "Aborted groupy-1. To undo, run: sh .groupy/groupy-1/undo-abort.sh",
        )
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main"}
        assert env.git_tags() == set()
        assert env.git_status() == ""

    # We look at the per-branch dir of groupy-1.
    #
    # It should be kept (with the logs, and so that the branch name is not
    # reused), and have the undo script.
    if env.step():
        assert env.file_exists(".groupy/groupy-1/last-run.yaml")
        assert env.file_exists(".groupy/groupy-1/undo-abort.sh")

    # We change our mind, and run the undo script.
    #
    # The branch and its tags should be back at the commits where they were.
    if env.step(
        env.run_shell("sh .groupy/groupy-1/undo-abort.sh"),
    ):
        assert env.git_branches() == {"main", "groupy-1"}
        assert env.branch_state("groupy-1") == env.remembered_branch

    # We run groupy switch groupy-1.
    #
    # The session should continue where it was.
    if env.step(
        env.run_groupy_command("switch", "groupy-1"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.git_branch() == "groupy-1"
        assert env.session.next_stage == "analyze-terminology"


class Env(TestEnv):
    pass
