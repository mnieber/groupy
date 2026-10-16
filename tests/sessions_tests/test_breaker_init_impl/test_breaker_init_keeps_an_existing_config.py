from sessions_tests.breaker_test_env import Context, TestEnv

CONFIG_YAML = """\
grouping_strategy: package
max_chunk_lines: 100
"""


def create_env(context: Context):
    return Env(context)


def test_breaker_init_keeps_an_existing_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with a committed config file that only sets the
    # grouping strategy and the maximum chunk size.
    if env.step(
        env.create_repo_with_target_code(),
        env.write_file(".breaker/config.yaml", CONFIG_YAML),
        env.commit_all("add breaker config"),
    ):
        pass

    # We run breaker init.
    #
    # It should keep the config file as it is.
    if env.step(
        env.run_breaker("init", "--target-dir=src"),
    ):
        assert env.read_file(".breaker/config.yaml") == CONFIG_YAML
        assert env.git_status() == ""

    # We load the config.
    #
    # The fields in the config file should have their value from the file, and
    # the other fields should have their default value.
    if env.step(
        env.load_config(),
    ):
        assert env.config.grouping_strategy == "package"
        assert env.config.max_chunk_lines == 100
        assert env.config.max_group_lines == 2000
        assert env.config.rfa_policy == (
            "breaker.claude_requests.policies.claude_rfa_policy:ClaudeRfaPolicy"
        )


class Env(TestEnv):
    pass
