from groupy_next_tests.groupy_next_test_env import Context, TestEnv, callback


def create_env(context: Context):
    return Env(context)


def test_groupy_next_cleans_up_after_ctrl_c(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, and the first stage is replaced
    # by a fake stage. The RFA of the only chunk adds a responsibility to
    # create_book, but the developer presses Ctrl+C after the node file was
    # changed and before Groupy commits it.
    if env.step(
        env.create_session(
            grouping_strategy="simple", max_group_lines=10000, max_chunk_lines=10000
        ),
        env.install_fake_stage(),
        env.script_rfa(
            "identify-helper-functions/group-1/chunk-1",
            callback(
                "add_responsibility",
                module_name="myapp/books.py",
                location="create_book",
                responsibility="Creates a book",
            ),
        ),
        env.press_ctrl_c_in_add_responsibility(),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next, as the developer does.
    #
    # Groupy should restore the working tree, report the stage as
    # interrupted (with KeyboardInterrupt as the error), and exit with code
    # 130. The session should be unchanged, so that groupy next can resume the
    # stage.
    if env.step(
        env.run_groupy_cli("next"),
        env.load_session(),
    ):
        assert env.exit_code == 130
        assert env.output_contains(
            "interrupted",
            "KeyboardInterrupt",
            "identify-helper-functions/group-1/chunk-1",
        )
        assert env.git_status() == ""
        assert env.git_head() == env.remembered_git_head
        assert env.responsibilities("myapp/books.py", "create_book") == []
        assert env.session.next_stage == "identify-helper-functions"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
