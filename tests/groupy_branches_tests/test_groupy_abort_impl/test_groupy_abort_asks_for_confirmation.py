from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_abort_asks_for_confirmation(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, which finished the stage
    # identify-helper-functions. We change the README without committing it.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_groupy("next"),
        env.append_to_file("README.md", "Work in progress.\n"),
        env.remember_branch("groupy-1"),
    ):
        pass

    # We run groupy abort, and answer no.
    #
    # Groupy should say that all commits of groupy-1 and the uncommitted
    # change will be lost, ask for confirmation, and change nothing.
    if env.step(
        env.run_groupy_command("abort", answer="n"),
    ):
        assert len(env.prompts) == 1
        assert env.output_contains(
            "all 8 commits on branch groupy-1 as well as these uncommitted " "changes:",
            "README.md",
        )
        assert env.git_branch() == "groupy-1"
        assert env.branch_state("groupy-1") == env.remembered_branch
        assert "Work in progress." in env.read_file("README.md")
        assert not env.file_exists(".groupy/groupy-1/undo-abort.sh")

    # We run groupy abort --force.
    #
    # Groupy should abort the branch without asking.
    if env.step(
        env.run_groupy_command("abort", "--force"),
    ):
        assert env.exit_code == 0
        assert env.prompts == []
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main"}
        assert env.git_tags() == set()
        assert env.git_status() == ""


class Env(TestEnv):
    pass
