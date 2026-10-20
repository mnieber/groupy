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
        env.script_first_chunk(),
        env.script_second_chunk(),
        env.run_groupy("next"),
        env.tag_head("groupy/groupy-1/analyze-terminology/start"),
    ):
        pass

    # We run groupy reset init --force.
    #
    # The repo should be back at the commit of groupy init, before the modules
    # were grouped, so that group-modules is the next stage again, and only the
    # groupy/groupy-1/init tag should be left.
    if env.step(
        env.run_groupy_reset("init", "--force"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.git_head() == env.tagged_commit("groupy/groupy-1/init")
        assert not env.file_exists(".groupy/groups.txt")
        assert env.git_status() == ""
        assert env.git_tags() == {"groupy/groupy-1/init"}
        assert env.session.next_stage == "group-modules"
        assert env.session.finished_chunks == []
        assert env.responsibilities("myapp/books.py", "create_book") == []


class Env(TestEnv):
    pass
