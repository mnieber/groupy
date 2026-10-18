from claude_policies_tests.claude_policies_test_env import (
    Context,
    TestEnv,
    run_callback,
)

RFA_ID = "identify-helper-functions/group-1/chunk-1"

BOOKS = "myapp/books.py"


def add_responsibility(location: str, responsibility: str):
    return run_callback(
        "add_responsibility",
        module_name=BOOKS,
        location=location,
        responsibility=responsibility,
    )


def create_env(context: Context):
    return Env(context)


def test_claude_policies_allow_one_retry_of_a_failed_callback(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses the Claude policies. In the RFA, the fake
    # claude twice runs a callback with an unknown location, each time
    # followed by a correct retry.
    if env.step(
        env.create_session_with_claude_policies(),
        env.script_claude(
            RFA_ID,
            add_responsibility("create_bok", "Creates a book"),
            add_responsibility("create_book", "Creates a book"),
            add_responsibility("Bok", "Holds a title"),
            add_responsibility("Book", "Holds a title"),
        ),
    ):
        pass

    # We run the RFA with the RFA policy.
    #
    # Each failed callback should have printed its error, with the offer to
    # retry once, and each retry should have succeeded. The request should not
    # have failed.
    if env.step(
        env.catch_error(env.run_rfa, RFA_ID),
        env.load_module_node(BOOKS),
    ):
        assert env.error is None
        outputs = env.command_outputs(RFA_ID)
        assert "NodeNotFoundError" in outputs[0]
        assert "retry it once" in outputs[0]
        assert outputs[1] == "OK\n"
        assert "retry it once" in outputs[2]
        assert outputs[3] == "OK\n"
        assert env.function_node("create_book").responsibilities == ["Creates a book"]
        assert env.class_node("Book").responsibilities == ["Holds a title"]
        assert not env.request_file_exists(RFA_ID, "failed-callback.yaml")
        assert env.git_status() == ""


class Env(TestEnv):
    pass
