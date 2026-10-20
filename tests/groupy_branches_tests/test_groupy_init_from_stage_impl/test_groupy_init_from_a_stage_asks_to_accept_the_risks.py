from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_from_a_stage_asks_to_accept_the_risks(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1.
    if env.step(
        env.create_session_with_two_chunks(),
        env.remember_git_head(),
    ):
        pass

    # We run groupy init --from-stage=group-modules without --accept-risks,
    # and decline the risks.
    #
    # Groupy should have asked to accept the risks, and changed nothing.
    if env.step(
        env.answer_prompts("n"),
        env.run_groupy_cli("init", "--from-stage=group-modules"),
    ):
        assert len(env.prompts) == 1
        assert env.git_branch() == "groupy-1"
        assert env.git_head() == env.remembered_git_head
        assert not env.file_exists(".groupy/groupy-2")

    # We run it again, and accept the risks.
    #
    # It should create the branch groupy-2.
    if env.step(
        env.answer_prompts("y"),
        env.run_groupy_cli("init", "--from-stage=group-modules"),
    ):
        assert env.exit_code == 0
        assert env.git_branch() == "groupy-2"


class Env(TestEnv):
    pass
