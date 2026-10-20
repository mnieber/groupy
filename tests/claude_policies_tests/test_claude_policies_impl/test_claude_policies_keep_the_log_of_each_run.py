import json

from claude_policies_tests.claude_policies_test_env import Context, TestEnv

RFA_ID = "identify-helper-functions/group-1/chunk-1"

# The session log of claude, with the cost of the session
SESSION_LOG = (
    json.dumps({"type": "system", "subtype": "init"})
    + "\n"
    + json.dumps({"type": "result", "subtype": "success", "total_cost_usd": 0.1})
    + "\n"
)


def create_env(context: Context):
    return Env(context)


def test_claude_policies_keep_the_log_of_each_run(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses the Claude policies, where the fake claude
    # answers the RFA with a session that costs 0.10 USD.
    if env.step(
        env.create_session_with_claude_policies(),
        env.script_claude(RFA_ID, stdout=SESSION_LOG),
    ):
        pass

    # We run the RFA twice (e.g. when an interrupted stage resumes).
    #
    # The log of the request should contain both sessions.
    if env.step(
        env.run_rfa(RFA_ID),
        env.run_rfa(RFA_ID),
    ):
        assert env.read_file(f".groupy/groupy-1/logs/{RFA_ID}.jsonl") == SESSION_LOG * 2

    # We run groupy status.
    #
    # It should report the costs of both sessions.
    if env.step(
        env.run_groupy_cli("status"),
    ):
        assert env.output_contains("0.20 USD")


class Env(TestEnv):
    pass
