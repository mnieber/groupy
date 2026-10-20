from groupy_branches_tests.groupy_branches_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_from_a_stage_of_another_branch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, which finished the stage
    # identify-helper-functions. We go back to main.
    if env.step(
        env.create_session_with_two_chunks(),
        env.run_groupy("next"),
        env.run_git("checkout", "main"),
    ):
        pass

    # We run groupy init --from-stage=groupy-1/group-modules.
    #
    # Groupy should have created groupy-2 at the start of group-modules on
    # groupy-1, with copies of the tags up to and including group-modules.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--from-stage=groupy-1/group-modules"),
        env.load_session(),
    ):
        assert env.git_branch() == "groupy-2"
        assert env.git_head() == env.tagged_commit(
            "groupy/groupy-1/group-modules/start"
        )
        assert env.branch_tags("groupy-2") == {"init", "group-modules/start"}
        assert env.session.next_stage == "group-modules"

    # We run groupy init --from-stage=groupy-1/init, while we are on groupy-2.
    #
    # Groupy should have created groupy-3 at the init commit of groupy-1, with
    # only a copy of the init tag.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--from-stage=groupy-1/init"),
        env.load_session(),
    ):
        assert env.git_branch() == "groupy-3"
        assert env.git_head() == env.tagged_commit("groupy/groupy-1/init")
        assert env.branch_tags("groupy-3") == {"init"}
        assert env.session.next_stage == "group-modules"


class Env(TestEnv):
    pass
