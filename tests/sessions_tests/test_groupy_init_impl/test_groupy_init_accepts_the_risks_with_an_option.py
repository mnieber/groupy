from sessions_tests.groupy_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_accepts_the_risks_with_an_option(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the target code. Groupy may not ask questions.
    if env.step(
        env.create_repo_with_target_code(),
        env.answer_prompts(None),
    ):
        pass

    # We run groupy init with --accept-risks (e.g. in a script).
    #
    # Groupy should start the session without explaining the risks or asking
    # for them to be accepted.
    if env.step(
        env.run_groupy_cli("init", "--target-dir=src", "--accept-risks"),
    ):
        assert env.exit_code == 0
        assert env.prompts == []
        assert "rope and Claude" not in env.output
        assert env.file_exists(".groupy/session.yaml")


class Env(TestEnv):
    pass
