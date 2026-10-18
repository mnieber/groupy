from claude_policies_tests.claude_policies_test_env import Context, TestEnv

# Sonnet for analyze-terminology, and the default model (haiku) otherwise
EXTRA_CONFIG = """\
claude_model_by_stage:
  analyze-terminology: sonnet
"""


def create_env(context: Context):
    return Env(context)


def test_claude_policies_use_the_model_of_the_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses the Claude policies, with the model haiku,
    # except for analyze-terminology, which uses sonnet. The fake claude
    # answers each request without callbacks.
    if env.step(
        env.create_session_with_claude_policies(EXTRA_CONFIG),
        env.script_claude("identify-helper-functions/group-1/chunk-1"),
        env.script_claude("analyze-terminology/group-1/chunk-1"),
        env.script_claude("analyze-terminology/group-1/chunk-1/rfr"),
    ):
        pass

    # We run an RFA in the first stage (identify-helper-functions).
    #
    # It has no model of its own, so it should use the default model.
    if env.step(
        env.run_rfa("identify-helper-functions/group-1/chunk-1"),
    ):
        assert env.claude_option(
            "identify-helper-functions/group-1/chunk-1", "--model"
        ) == ["haiku"]

    # We move on to analyze-terminology, and run an RFA and an RFR.
    #
    # Both should use the model of the stage.
    if env.step(
        env.set_next_stage("analyze-terminology"),
        env.load_session(),
        env.run_rfa("analyze-terminology/group-1/chunk-1"),
        env.run_rfr("analyze-terminology/group-1/chunk-1/rfr"),
    ):
        assert env.claude_option("analyze-terminology/group-1/chunk-1", "--model") == [
            "sonnet"
        ]
        assert env.claude_option(
            "analyze-terminology/group-1/chunk-1/rfr", "--model"
        ) == ["sonnet"]


class Env(TestEnv):
    pass
