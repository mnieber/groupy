from groupy_next_tests.groupy_next_test_env import Context, TestEnv, callback


def create_env(context: Context):
    return Env(context)


def test_groupy_next_guides_the_developer(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, with the package grouping
    # strategy, so that the modules of myapp (group 1) and of myapp/chapters
    # (group 2) are in different chunks. The first stage is replaced by a fake
    # stage that makes an RFA per chunk. Only the RFA of the first chunk has a
    # script.
    if env.step(
        env.create_session(
            grouping_strategy="package", max_group_lines=10000, max_chunk_lines=10000
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
    ):
        pass

    # We run groupy next, as the developer does.
    #
    # The RFA of the second chunk has no script, so the stage should be
    # interrupted. Groupy should print the error instead of a traceback: the
    # stage, the request id of the chunk, the error class and message, and how
    # to resume the stage. It should exit with code 1.
    if env.step(
        env.run_groupy_cli("next"),
    ):
        assert env.exit_code == 1
        assert env.output_contains(
            "identify-helper-functions",
            "interrupted",
            "identify-helper-functions/group-2/chunk-1",
            "UnscriptedRequestError",
            "There is no script for the RFA",
            "groupy next",
        )
        assert "Traceback" not in env.output
        assert env.git_status() == ""

    # We add a script for the second chunk, and run groupy next again.
    #
    # Groupy should resume and finish the stage, and print a report: the
    # stage that finished, the number of commits that the stage made (two for
    # each chunk, and one to finish the stage), what to review, and which
    # stage the next groupy next will start.
    if env.step(
        env.script_rfa(
            "identify-helper-functions/group-2/chunk-1",
            callback(
                "add_responsibility",
                module_name="myapp/chapters/create_chapter.py",
                location="create_chapter",
                responsibility="Creates a chapter",
            ),
        ),
        env.run_groupy_cli("next"),
    ):
        assert env.exit_code == 0
        assert env.output_contains(
            "identify-helper-functions",
            "finished",
            "5 commits",
            "helper_function_nodes",
            "analyze-terminology",
        )


class Env(TestEnv):
    pass
