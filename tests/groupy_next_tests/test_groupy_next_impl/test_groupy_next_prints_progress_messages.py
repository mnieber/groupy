from groupy_next_tests.groupy_next_test_env import Context, TestEnv, callback

RFA_ID_1 = "identify-helper-functions/group-1/chunk-1"

RFA_ID_2 = "identify-helper-functions/group-2/chunk-1"


def create_env(context: Context):
    return Env(context)


def test_groupy_next_prints_progress_messages(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, with the package grouping
    # strategy (two chunks). The first stage is replaced by a fake stage that
    # makes an RFA per chunk. Only the RFA of the first chunk has a script.
    if env.step(
        env.create_session(
            grouping_strategy="package", max_group_lines=10000, max_chunk_lines=10000
        ),
        env.install_fake_stage(),
        env.script_rfa(
            RFA_ID_1,
            callback(
                "add_responsibility",
                module_name="myapp/books.py",
                location="create_book",
                responsibility="Creates a book",
            ),
        ),
    ):
        pass

    # We run groupy next, which is interrupted at the second chunk.
    #
    # Groupy should have printed a progress message on stderr at the start of
    # each chunk, with the request id and the position of the chunk.
    if env.step(
        env.run_groupy_next_and_catch_error(),
    ):
        assert env.error is not None
        assert env.error_lines == [f"{RFA_ID_1} (1/2)", f"{RFA_ID_2} (2/2)"]
        assert f"{RFA_ID_1} (1/2)" not in env.output_lines

    # We add a script for the second chunk, and run groupy next again.
    #
    # The finished chunk is skipped without a message, so Groupy should only
    # print the message of the second chunk.
    if env.step(
        env.script_rfa(
            RFA_ID_2,
            callback(
                "add_responsibility",
                module_name="myapp/chapters/create_chapter.py",
                location="create_chapter",
                responsibility="Creates a chapter",
            ),
        ),
        env.run_groupy_next(),
    ):
        assert env.error_lines == [f"{RFA_ID_2} (2/2)"]


class Env(TestEnv):
    pass
