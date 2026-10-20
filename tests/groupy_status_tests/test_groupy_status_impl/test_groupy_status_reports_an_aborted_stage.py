from groupy_status_tests.groupy_status_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_status_reports_an_aborted_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package. We simulate a groupy next that
    # was killed during the first chunk: it tagged the start of the stage,
    # left the last-run file with the result running, and left a changed file.
    if env.step(
        env.create_session(
            grouping_strategy="simple", max_group_lines=10000, max_chunk_lines=10000
        ),
        env.tag_head("groupy/groupy-1/identify-helper-functions/start"),
        env.write_last_run(
            stage="identify-helper-functions",
            result="running",
            request_id="identify-helper-functions/group-1/chunk-1",
        ),
        env.append_to_file("src/myapp/books.py", "\nDEFAULT_TITLE = 'Untitled'\n"),
    ):
        pass

    # We run groupy status.
    #
    # It should print that the last run was aborted, that groupy next will
    # resume the stage, and that the working tree is not clean, with a hint
    # to commit, stash or reset.
    if env.step(
        env.run_groupy_cli("status"),
    ):
        assert env.exit_code == 0
        assert env.output_contains(
            "aborted",
            "identify-helper-functions/group-1/chunk-1",
            "will resume",
            "commit",
            "stash",
            "groupy reset",
        )


class Env(TestEnv):
    pass
