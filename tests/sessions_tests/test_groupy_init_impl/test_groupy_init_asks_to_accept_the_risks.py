from sessions_tests.groupy_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_asks_to_accept_the_risks(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the target code. The developer will not accept
    # the risks.
    if env.step(
        env.create_repo_with_target_code(),
        env.answer_prompts("n"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy init, as the developer does.
    #
    # Groupy should explain the risks (errors in the code, for which the
    # developer remains responsible, and the costs of Claude), and ask whether
    # the developer accepts them. Since the developer doesn't, it should
    # change nothing, and point to --accept-risks.
    if env.step(
        env.run_groupy_cli("init", "--target-dir=src"),
    ):
        assert env.exit_code == 1
        assert len(env.prompts) == 1
        assert env.output_contains(
            "rope and Claude",
            "errors",
            "responsible for the correctness",
            "costs",
            "cancelled",
            "--accept-risks",
        )
        assert not env.file_exists(".groupy/session.yaml")
        assert env.git_branch() == "main"
        assert env.git_head() == env.remembered_git_head

    # The developer accepts the risks, and runs groupy init again.
    #
    # It should start the session.
    if env.step(
        env.answer_prompts("y"),
        env.run_groupy_cli("init", "--target-dir=src"),
    ):
        assert env.exit_code == 0
        assert env.file_exists(".groupy/session.yaml")
        assert env.git_branch() == "groupy-1"


class Env(TestEnv):
    pass
