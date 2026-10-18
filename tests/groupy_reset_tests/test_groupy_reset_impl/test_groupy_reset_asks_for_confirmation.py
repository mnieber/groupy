from groupy_reset_tests.groupy_reset_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_reset_asks_for_confirmation(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session with two chunks, and only the RFA of the first chunk
    # has a script. We run groupy next, which is interrupted at the second
    # chunk.
    if env.step(
        env.create_session_with_two_chunks(),
        env.remember_git_head(),
        env.script_first_chunk(),
        env.run_groupy_and_catch_error("next"),
    ):
        pass

    # The developer commits a repair, and changes the README without
    # committing it. Then we run groupy reset, and answer no.
    #
    # Groupy should list what will be lost: the commit of the developer and
    # the uncommitted change, but not the commits of Groupy. Then it should ask
    # for confirmation, and change nothing.
    if env.step(
        env.append_to_file("src/myapp/books.py", "\nDEFAULT_TITLE = 'Untitled'\n"),
        env.commit_all("repair books.py"),
        env.append_to_file("README.md", "Work in progress.\n"),
        env.remember_head_before_reset(),
        env.run_groupy_reset(answer="n"),
    ):
        assert len(env.prompts) == 1
        assert env.output_contains("repair books.py", "README.md")
        assert "add_responsibility" not in env.output
        assert "finish group-1/chunk-1" not in env.output
        assert env.git_head() == env.head_before_reset
        assert "Work in progress." in env.read_file("README.md")
        assert "groupy/identify-helper-functions/start" in env.git_tags()

    # We run groupy reset again, and answer yes.
    #
    # Groupy should reset the stage, which discards the commit of the
    # developer and the uncommitted change.
    if env.step(
        env.run_groupy_reset(answer="y"),
    ):
        assert env.exit_code == 0
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""
        assert "Work in progress." not in env.read_file("README.md")


class Env(TestEnv):
    pass
