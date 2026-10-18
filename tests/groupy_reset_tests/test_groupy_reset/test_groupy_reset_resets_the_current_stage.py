from groupy_reset_tests.groupy_reset_test_env import (
    RFA_ID_1,
    RFA_ID_2,
    Context,
    TestEnv,
)


def create_env(context: Context):
    return Env(context)


def test_groupy_reset_resets_the_current_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session with two chunks, and only the RFA of the first chunk
    # has a script. The developer commits a review edit before the first
    # stage.
    if env.step(
        env.create_session_with_two_chunks(),
        env.script_first_chunk(),
        env.append_to_file("README.md", "Reviewed the node files.\n"),
        env.commit_all("review the node files"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next, which is interrupted at the second chunk. The
    # developer commits a repair.
    if env.step(
        env.run_groupy_and_catch_error("next"),
        env.append_to_file("src/myapp/books.py", "\nDEFAULT_TITLE = 'Untitled'\n"),
        env.commit_all("repair books.py"),
    ):
        assert env.git_tags() == {
            "groupy/init",
            "groupy/group-modules/start",
            "groupy/identify-helper-functions/start",
        }

    # We run groupy reset --yes.
    #
    # Groupy should list the commit of the developer that will be lost, and
    # print the previous head, so that the reset can be undone. It should not
    # ask for confirmation. The repo should be back at the start of the stage,
    # which keeps the review edit, and the tag of the stage should be gone.
    if env.step(
        env.remember_head_before_reset(),
        env.run_groupy_reset("--yes"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.output_contains("repair books.py", env.head_before_reset[:7])
        assert env.prompts == []
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""
        assert "Reviewed the node files." in env.read_file("README.md")
        assert env.git_tags() == {"groupy/init", "groupy/group-modules/start"}
        assert env.session.next_stage == "identify-helper-functions"
        assert env.session.finished_chunks == []

    # We add a script for the second chunk, and run groupy next.
    #
    # Groupy should run the stage anew, starting at the first chunk.
    if env.step(
        env.script_second_chunk(),
        env.clear_rfa_requests(),
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.rfa_ids() == [RFA_ID_1, RFA_ID_2]
        assert env.session.next_stage == "analyze-terminology"


class Env(TestEnv):
    pass
