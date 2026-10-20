from claude_policies_tests.claude_policies_test_env import (
    Context,
    TestEnv,
    run_callback,
)

from groupy.call_graph.enums import CallScopes
from groupy.call_graph.models.call_graph_view import (
    CallGraphView,
    CallView,
    FunctionView,
)

RFA_ID = "identify-helper-functions/group-1/chunk-1"

BOOKS = "myapp/books.py"

# A context with a model, which the policy writes as plain data
CONTEXT = {
    "call_graph_view": CallGraphView(
        function_views=[
            FunctionView(
                location="myapp/books.py:_normalize_title",
                callers=[
                    CallView(
                        location="myapp/books.py:create_book",
                        scope=CallScopes.SAME_MODULE,
                        is_certain=True,
                    )
                ],
            )
        ]
    )
}


def create_env(context: Context):
    return Env(context)


def test_claude_rfa_policy_runs_claude_with_the_request(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses the Claude policies with the model haiku,
    # where the fake claude answers the RFA with a query and a node edit.
    if env.step(
        env.create_session_with_claude_policies(),
        env.script_claude(
            RFA_ID,
            run_callback("get_source", location="myapp/books.py:create_book"),
            run_callback(
                "add_responsibility",
                module_name=BOOKS,
                location="create_book",
                responsibility="Creates a book",
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run the RFA with the RFA policy.
    #
    # The policy should have run claude in headless mode, with the model of
    # the config. Claude may only read files and run groupy callbacks, and
    # gets the prompt of the RFA, followed by the preamble that explains how
    # to read the context and run callbacks.
    if env.step(
        env.run_rfa(RFA_ID, CONTEXT),
    ):
        assert env.claude_option(RFA_ID, "--model") == ["haiku"]
        assert env.claude_option(RFA_ID, "--tools") == ["Read,Glob,Grep,Bash"]
        assert env.claude_option(RFA_ID, "--allowedTools") == [
            "Read",
            "Glob",
            "Grep",
            "Bash(groupy callback:*)",
        ]
        assert env.claude_option(RFA_ID, "--permission-mode") == ["dontAsk"]
        prompt = env.claude_prompt(RFA_ID)
        assert prompt.startswith("Analyze the code")
        assert f".groupy/groupy-1/requests/{RFA_ID}/context.yaml" in prompt
        assert "groupy callback <name> --args" in prompt
        assert "add_responsibility(module_name: str" in prompt
        assert env.claude_record(RFA_ID)["env"]["GROUPY_IN_RFR"] == ""

    # We look at the context file of the request.
    #
    # It should contain the context, with the model as plain data.
    if env.step():
        function_view = env.request_context(RFA_ID)["call_graph_view"][
            "function_views"
        ][0]
        assert function_view["location"] == "myapp/books.py:_normalize_title"
        assert function_view["callers"][0]["scope"] == "same-module"

    # We look at the outputs of the callbacks.
    #
    # The query should have printed the source, and the node edit OK. The
    # node edit should have been committed, as in any RFA.
    if env.step(
        env.load_module_node(BOOKS),
    ):
        assert env.command_outputs(RFA_ID) == [
            "def create_book(title):\n    return Book(_normalize_title(title))\n",
            "OK\n",
        ]
        assert env.function_node("create_book").responsibilities == ["Creates a book"]
        assert env.commit_messages_since_remembered_head() == [
            "identify-helper-functions: add_responsibility"
        ]
        assert env.git_status() == ""

    # We look at the log of the session.
    #
    # The output of claude should be kept in the log dir, which is not
    # committed.
    if env.step():
        assert env.file_exists(f".groupy/groupy-1/logs/{RFA_ID}.jsonl")


class Env(TestEnv):
    pass
