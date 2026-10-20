from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_abort_of_another_branch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, which finished the stage
    # identify-helper-functions. We start groupy-2 at the start of
    # identify-helper-functions, so that groupy-2 shares the init commit and
    # the two commits of group-modules with groupy-1. On groupy-2, we change
    # the README without committing it.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_groupy("next"),
        env.run_groupy(
            "init", "--accept-risks", "--from-stage=identify-helper-functions"
        ),
        env.append_to_file("README.md", "Work in progress.\n"),
        env.remember_branch("groupy-2"),
    ):
        assert env.git_branch() == "groupy-2"

    # We run groupy abort groupy-1, and answer yes.
    #
    # Only the five commits of identify-helper-functions are on no other
    # branch, so Groupy should say that these will be lost. The uncommitted
    # change is on groupy-2, so it should not be lost. Groupy should delete
    # groupy-1 and its tags, and stay on groupy-2.
    if env.step(
        env.run_groupy_command("abort", "groupy-1", answer="y"),
    ):
        assert env.exit_code == 0
        assert len(env.prompts) == 1
        assert env.output_contains(
            "all 5 commits on branch groupy-1",
            "Aborted groupy-1. To undo, run: sh .groupy/groupy-1/undo-abort.sh",
        )
        assert "uncommitted" not in env.output
        assert env.git_branch() == "groupy-2"
        assert env.git_branches() == {"main", "groupy-2"}
        assert env.branch_tags("groupy-1") == set()
        assert env.branch_state("groupy-2") == env.remembered_branch
        assert "Work in progress." in env.read_file("README.md")

    # We run groupy abort groupy-2, while we are on groupy-2, and answer yes.
    #
    # This is the same as groupy abort: now that groupy-1 is gone, the three
    # commits of groupy-2 are on no other branch, and the uncommitted change
    # will be lost too. Groupy should go back to the base branch.
    if env.step(
        env.run_groupy_command("abort", "groupy-2", answer="y"),
    ):
        assert env.exit_code == 0
        assert env.output_contains(
            "all 3 commits on branch groupy-2 as well as these uncommitted " "changes:",
            "README.md",
        )
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main"}
        assert env.git_tags() == set()
        assert env.git_status() == ""


class Env(TestEnv):
    pass
