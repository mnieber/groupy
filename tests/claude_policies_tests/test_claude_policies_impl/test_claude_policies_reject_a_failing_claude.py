from claude_policies_tests.claude_policies_test_env import Context, TestEnv

from groupy.claude_requests.actions.run_claude import ClaudeRequestError

RFA_ID = "identify-helper-functions/group-1/chunk-1"


def create_env(context: Context):
    return Env(context)


def test_claude_policies_reject_a_failing_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses the Claude policies, where the fake claude
    # fails with exit code 2 and an error message.
    if env.step(
        env.create_session_with_claude_policies(),
        env.script_claude(RFA_ID, exit_code=2, stderr="Credit balance is too low"),
    ):
        pass

    # We run the RFA with the RFA policy.
    #
    # The policy should raise a ClaudeRequestError with the request id, the
    # exit code and the error message.
    if env.step(
        env.catch_error(env.run_rfa, RFA_ID),
    ):
        assert isinstance(env.error, ClaudeRequestError)
        assert RFA_ID in str(env.error)
        assert "exit code 2" in str(env.error)
        assert "Credit balance is too low" in str(env.error)


class Env(TestEnv):
    pass
