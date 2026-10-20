from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_switch_asks_to_discard_uncommitted_changes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have sessions on branches groupy-1 and groupy-2, and we are on
    # groupy-2. Groupy left a file in the per-branch dir of groupy-2. We change
    # the README without committing it, and add an untracked file.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.write_file(".groupy/groupy-2/last-run.yaml", "result: finished\n"),
        env.append_to_file("README.md", "Work in progress.\n"),
        env.write_file("notes.txt", "Some notes.\n"),
        env.remember_git_head(),
    ):
        assert env.git_branch() == "groupy-2"

    # We run groupy switch groupy-1, and answer no.
    #
    # Groupy should list the uncommitted changes (there are no commits to
    # lose), ask for confirmation, and change nothing.
    if env.step(
        env.run_groupy_command("switch", "groupy-1", answer="n"),
    ):
        assert len(env.prompts) == 1
        assert env.output_contains(
            "these uncommitted changes:", "README.md", "notes.txt"
        )
        assert "commits" not in env.output
        assert env.git_branch() == "groupy-2"
        assert env.git_head() == env.remembered_git_head
        assert "Work in progress." in env.read_file("README.md")
        assert env.file_exists("notes.txt")

    # We run groupy switch groupy-1 again, and answer yes.
    #
    # Groupy should discard the changes and switch. The per-branch dir of
    # groupy-2 is not part of the changes, so it should be kept.
    if env.step(
        env.run_groupy_command("switch", "groupy-1", answer="y"),
    ):
        assert env.exit_code == 0
        assert env.git_branch() == "groupy-1"
        assert env.git_status() == ""
        assert "Work in progress." not in env.read_file("README.md")
        assert not env.file_exists("notes.txt")
        assert env.file_exists(".groupy/groupy-2/last-run.yaml")

    # We change the README again, and run groupy switch groupy-2 --force.
    #
    # Groupy should discard the change and switch, without asking.
    if env.step(
        env.append_to_file("README.md", "Work in progress.\n"),
        env.run_groupy_command("switch", "groupy-2", "--force"),
    ):
        assert env.exit_code == 0
        assert env.prompts == []
        assert env.git_branch() == "groupy-2"
        assert env.git_status() == ""


class Env(TestEnv):
    pass
