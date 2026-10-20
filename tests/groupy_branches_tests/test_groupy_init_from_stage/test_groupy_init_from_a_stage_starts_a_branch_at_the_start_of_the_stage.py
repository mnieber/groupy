from groupy_branches_tests.groupy_branches_test_env import (
    RFA_ID_1,
    RFA_ID_2,
    Context,
    TestEnv,
)


def create_env(context: Context):
    return Env(context)


def test_groupy_init_from_a_stage_starts_a_branch_at_the_start_of_the_stage(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session on branch groupy-1, with two chunks. The developer
    # commits a review edit before the first stage, and runs groupy next,
    # which finishes the stage identify-helper-functions.
    if env.step(
        env.create_session_with_two_chunks(),
        env.append_to_file("README.md", "Reviewed the node files.\n"),
        env.commit_all("review the node files"),
        env.remember_git_head(),
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.git_branch() == "groupy-1"
        assert env.session.next_stage == "analyze-terminology"
        assert env.branch_tags("groupy-1") == {
            "init",
            "group-modules/start",
            "identify-helper-functions/start",
        }

    # We want to redo identify-helper-functions on a new branch, so we run
    # groupy init --from-stage=identify-helper-functions.
    #
    # Groupy should have created the branch groupy-2 at the start of the stage
    # (which has the review edit), without a new commit. The session should
    # be at the start of the stage.
    if env.step(
        env.run_groupy(
            "init", "--accept-risks", "--from-stage=identify-helper-functions"
        ),
        env.load_session(),
    ):
        assert env.git_branch() == "groupy-2"
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""
        assert env.file_exists(".groupy/groupy-2")
        assert env.session.next_stage == "identify-helper-functions"
        assert env.session.finished_chunks == []
        assert env.session.base_branch == "main"

    # We look at the tags.
    #
    # groupy-2 should have copies of the init tag and the start tags of the
    # stages up to and including identify-helper-functions, at the same
    # commits as those of groupy-1. The tags of groupy-1 should be kept.
    if env.step():
        assert env.branch_tags("groupy-2") == {
            "init",
            "group-modules/start",
            "identify-helper-functions/start",
        }
        for tag in env.branch_tags("groupy-2"):
            assert env.tagged_commit(f"groupy/groupy-2/{tag}") == env.tagged_commit(
                f"groupy/groupy-1/{tag}"
            )
        assert env.branch_tags("groupy-1") == env.branch_tags("groupy-2")

    # We run groupy next on groupy-2.
    #
    # Groupy should run identify-helper-functions anew, starting at the first
    # chunk. It should resume the stage (the start tag exists), so the tag
    # should stay where it is.
    if env.step(
        env.clear_rfa_requests(),
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.rfa_ids() == [RFA_ID_1, RFA_ID_2]
        assert env.session.next_stage == "analyze-terminology"
        assert (
            env.tagged_commit("groupy/groupy-2/identify-helper-functions/start")
            == env.remembered_git_head
        )


class Env(TestEnv):
    pass
