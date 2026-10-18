from groupy_next_tests.groupy_next_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_next_prints_a_hint_for_a_dirty_working_tree(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, and the first stage is replaced
    # by a fake stage. We change a tracked file without committing it.
    if env.step(
        env.create_session(grouping_strategy="simple"),
        env.install_fake_stage(),
        env.append_to_file("src/myapp/books.py", "\nDEFAULT_TITLE = 'Untitled'\n"),
    ):
        pass

    # We run groupy next, as the developer does.
    #
    # Groupy should print the error, with a hint to commit or stash the
    # changes, or to reset the stage. It should exit with code 1, without
    # running the stage.
    if env.step(
        env.run_groupy_cli("next"),
    ):
        assert env.exit_code == 1
        assert env.output_contains(
            "DirtyWorkingTreeError", "commit", "stash", "groupy reset"
        )
        assert "Traceback" not in env.output
        assert env.rfa_ids() == []


class Env(TestEnv):
    pass
