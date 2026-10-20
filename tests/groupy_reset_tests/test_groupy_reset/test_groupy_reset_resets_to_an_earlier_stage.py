from groupy_reset_tests.groupy_reset_test_env import (
    RFA_ID_1,
    RFA_ID_2,
    Context,
    TestEnv,
)


def create_env(context: Context):
    return Env(context)


def test_groupy_reset_resets_to_an_earlier_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session with two chunks. The developer commits a review edit
    # before the first stage, and runs groupy next, which finishes the stage
    # identify-helper-functions.
    if env.step(
        env.create_session_with_two_chunks(),
        env.script_first_chunk(),
        env.script_second_chunk(),
        env.append_to_file("README.md", "Reviewed the node files.\n"),
        env.commit_all("review the node files"),
        env.remember_git_head(),
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "analyze-terminology"

    # We are not happy with the result, so we run groupy reset
    # identify-helper-functions, and answer yes.
    #
    # Groupy should say that the commits of the stage will be lost, and ask
    # for confirmation. The repo should be back at the start of
    # identify-helper-functions, which keeps the review edit, and the tag of
    # the stage should be gone.
    if env.step(
        env.run_groupy_reset("identify-helper-functions", answer="y"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert len(env.prompts) == 1
        assert env.output_contains(
            "all 5 commits since the start of identify-helper-functions"
        )
        assert env.git_head() == env.remembered_git_head
        assert "Reviewed the node files." in env.read_file("README.md")
        assert env.git_tags() == {
            "groupy/groupy-1/init",
            "groupy/groupy-1/group-modules/start",
        }
        assert env.session.next_stage == "identify-helper-functions"

    # We run groupy next.
    #
    # Groupy should run identify-helper-functions anew.
    if env.step(
        env.clear_rfa_requests(),
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.rfa_ids() == [RFA_ID_1, RFA_ID_2]
        assert env.session.next_stage == "analyze-terminology"

    # We run groupy reset group-modules --force.
    #
    # The repo should be back at the start of group-modules, before the
    # modules were grouped, and only the init tag should be left.
    if env.step(
        env.run_groupy_reset("group-modules", "--force"),
        env.load_session(),
    ):
        assert env.exit_code == 0
        assert env.git_head() == env.tagged_commit("groupy/groupy-1/init")
        assert not env.file_exists(".groupy/groups.txt")
        assert env.git_tags() == {"groupy/groupy-1/init"}
        assert env.session.next_stage == "group-modules"


class Env(TestEnv):
    pass
