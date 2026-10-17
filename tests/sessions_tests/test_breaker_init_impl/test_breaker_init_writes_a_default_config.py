from sessions_tests.breaker_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_breaker_init_writes_a_default_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo without a config file, and we run breaker init.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_breaker("init", "--target-dir=src"),
    ):
        assert ".breaker/config.yaml" in env.files_in_head_commit()

    # We load the config.
    #
    # Every field should have its default value.
    if env.step(
        env.load_config(),
    ):
        assert env.config.rfa_policy == (
            "breaker.claude_requests.policies.claude_rfa_policy:ClaudeRfaPolicy"
        )
        assert env.config.rfr_policy == (
            "breaker.claude_requests.policies.claude_rfr_policy:ClaudeRfrPolicy"
        )
        assert env.config.grouping_policy == (
            "breaker.groups.policies.claude_grouping_policy:ClaudeGroupingPolicy"
        )
        assert env.config.refactoring_policy == (
            "breaker.renamings.policies.rope_refactoring_policy:"
            "RopeRefactoringPolicy"
        )
        assert env.config.grouping_strategy == "package"
        assert env.config.max_group_lines == 2000
        assert env.config.max_chunk_lines == 500

    # We look at the config file.
    #
    # It should list every field, so that the developer can see what can be
    # configured.
    if env.step():
        text = env.read_file(".breaker/config.yaml")
        for field in (
            "rfa_policy",
            "rfr_policy",
            "grouping_policy",
            "refactoring_policy",
            "grouping_strategy",
            "max_group_lines",
            "max_chunk_lines",
        ):
            assert f"{field}:" in text


class Env(TestEnv):
    pass
