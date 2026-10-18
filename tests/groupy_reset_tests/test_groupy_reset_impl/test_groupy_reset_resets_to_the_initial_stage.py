from groupy_reset_tests.groupy_reset_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_reset_resets_to_the_initial_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session with two chunks. The first stage has finished, and
    # the second stage has started (which tagged its start).
    if env.step(
        env.create_session_with_two_chunks(),
        env.remember_git_head(),
        env.script_first_chunk(),
        env.script_second_chunk(),
        env.run_groupy("next"),
        env.tag_head("groupy/analyze-terminology/start"),
    ):
        pass

    # We run groupy reset --init --yes.
    #
    # The repo should be back at the commit of groupy init, so that the first
    # stage is the next stage again, and only the groupy/init tag should be
    # left.
    if env.step(
        env.run_groupy_reset("--init", "--yes"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.git_head() == env.remembered_git_head
        assert env.git_head() == env.tagged_commit("groupy/init")
        assert env.git_status() == ""
        assert env.git_tags() == {"groupy/init"}
        assert env.session.next_stage == "identify-helper-functions"
        assert env.session.finished_chunks == []
        assert env.responsibilities("myapp/books.py", "create_book") == []


class Env(TestEnv):
    pass
