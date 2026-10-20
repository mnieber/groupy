from groupy_reset_tests.groupy_reset_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_reset_when_nothing_is_lost(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session with two chunks, but no scripts. We run groupy next,
    # which is interrupted at the first chunk, before its first commit.
    if env.step(
        env.create_session_with_two_chunks(),
        env.remember_git_head(),
        env.run_groupy_and_catch_error("next"),
    ):
        assert env.error is not None
        assert env.git_head() == env.remembered_git_head
        assert "groupy/groupy-1/identify-helper-functions/start" in env.git_tags()

    # We run groupy reset, without answering questions.
    #
    # The repo is already at the start of the stage, and the working tree is
    # clean, so Groupy should say so, without asking for confirmation and
    # without an undo hint.
    if env.step(
        env.run_groupy_reset(),
    ):
        assert env.exit_code == 0
        assert env.prompts == []
        assert env.output_contains(
            "The repo is already at the start of identify-helper-functions."
        )
        assert "git reset --hard" not in env.output
        assert env.git_head() == env.remembered_git_head

    # We change the README without committing it, and run groupy reset, and
    # answer yes.
    #
    # Groupy should only list the uncommitted change (there are no commits to
    # lose), ask for confirmation, and discard the change.
    if env.step(
        env.append_to_file("README.md", "Work in progress.\n"),
        env.run_groupy_reset(answer="y"),
    ):
        assert env.exit_code == 0
        assert len(env.prompts) == 1
        assert env.output_contains("these uncommitted changes:", "README.md")
        assert "commits since" not in env.output
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""


class Env(TestEnv):
    pass
