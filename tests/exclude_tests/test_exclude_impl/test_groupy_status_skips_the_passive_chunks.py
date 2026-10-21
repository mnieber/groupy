from exclude_tests.exclude_test_env import Context, TestEnv

RFA_ID_1 = "identify-helper-functions/group-1/chunk-1"

RFA_ID_2 = "identify-helper-functions/group-2/chunk-1"

RFA_ID_3 = "identify-helper-functions/group-3/chunk-1"


def create_env(context: Context):
    return Env(context)


def test_groupy_status_skips_the_passive_chunks(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that excludes the reports package, so that the files
    # of group-3/chunk-1 are all passive. Only the RFA of the first chunk has a
    # script.
    if env.step(
        env.create_session_with_reports("myapp/reports/**"),
        env.script_rfa(RFA_ID_1),
    ):
        pass

    # We run groupy next, which is interrupted at the second chunk, and then
    # groupy status.
    #
    # It should list the second chunk as remaining, but not the third chunk,
    # which gets no RFA.
    if env.step(
        env.run_groupy_and_catch_error("next"),
        env.run_groupy_cli("status"),
    ):
        assert env.exit_code == 0
        assert env.output_contains(f"Finished chunks: {RFA_ID_1}\n")
        assert env.output_contains(f"Remaining chunks: {RFA_ID_2}\n")
        assert RFA_ID_3 not in env.output


class Env(TestEnv):
    pass
