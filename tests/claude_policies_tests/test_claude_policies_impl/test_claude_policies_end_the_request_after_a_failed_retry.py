from claude_policies_tests.claude_policies_test_env import (
    Context,
    TestEnv,
    run_callback,
)

from groupy.nodes.utils.exceptions import NodeNotFoundError

RFA_ID = "identify-helper-functions/group-1/chunk-1"

BOOKS = "myapp/books.py"


def add_responsibility(location: str):
    return run_callback(
        "add_responsibility",
        module_name=BOOKS,
        location=location,
        responsibility="Creates a book",
    )


def create_env(context: Context):
    return Env(context)


def test_claude_policies_end_the_request_after_a_failed_retry(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses the Claude policies. In the RFA, the fake
    # claude runs a callback with an unknown location, retries it with
    # another unknown location, and then runs a correct callback.
    if env.step(
        env.create_session_with_claude_policies(),
        env.script_claude(
            RFA_ID,
            add_responsibility("create_bok"),
            add_responsibility("create_boook"),
            add_responsibility("create_book"),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run the RFA with the RFA policy.
    #
    # The failed retry should have ended the request: Groupy should have told
    # Claude to stop, and refused the next callback. The policy should raise
    # the error of the failed retry, and leave a clean working tree.
    if env.step(
        env.catch_error(env.run_rfa, RFA_ID),
        env.load_module_node(BOOKS),
    ):
        assert isinstance(env.error, NodeNotFoundError)
        assert "create_boook" in str(env.error)
        outputs = env.command_outputs(RFA_ID)
        assert "retry it once" in outputs[0]
        assert "create_boook" in outputs[1]
        assert "Stop processing this request" in outputs[1]
        assert "The callback failed" not in outputs[2]
        assert "Stop processing this request" in outputs[2]
        assert env.function_node("create_book").responsibilities == []
        assert env.commit_messages_since_remembered_head() == []
        assert env.git_status() == ""


class Env(TestEnv):
    pass
