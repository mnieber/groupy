from sessions_tests.groupy_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_groupy_init_starts_a_new_branch_per_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package in the src dir.
    if env.step(
        env.create_repo_with_target_code(),
        env.remember_git_head(),
    ):
        assert env.git_branch() == "main"

    # We run groupy init without a branch name.
    #
    # Groupy should have created the branch groupy-1 from main, with its
    # per-branch dir, and tagged the init commit with a tag that includes the
    # branch name. The session should record main as the base branch.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.load_session(),
    ):
        assert env.git_branch() == "groupy-1"
        assert env.commit_of("groupy-1~1") == env.remembered_git_head
        assert env.file_exists(".groupy/groupy-1")
        assert env.git_tags() == {"groupy/groupy-1/init"}
        assert env.tagged_commit("groupy/groupy-1/init") == env.git_head()
        assert env.session.base_branch == "main"

    # We run groupy init again, while we are on groupy-1.
    #
    # Groupy should have created the branch groupy-2. It should start from the
    # base branch, not from groupy-1.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        assert env.git_branch() == "groupy-2"
        assert env.commit_of("groupy-2~1") == env.remembered_git_head
        assert env.git_branches() == {"main", "groupy-1", "groupy-2"}
        assert env.file_exists(".groupy/groupy-2")
        assert env.git_tags() == {"groupy/groupy-1/init", "groupy/groupy-2/init"}

    # We go back to main, and delete the branch groupy-2 (as groupy abort
    # will do, it keeps the per-branch dir).
    if env.step(
        env.run_git("checkout", "main"),
        env.run_git("branch", "-D", "groupy-2"),
        env.run_git("tag", "-d", "groupy/groupy-2/init"),
    ):
        assert env.file_exists(".groupy/groupy-2")

    # We run groupy init again.
    #
    # Groupy never reuses a branch name: the per-branch dir of groupy-2 is
    # still there, so the new branch should be groupy-3.
    if env.step(
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        assert env.git_branch() == "groupy-3"
        assert env.commit_of("groupy-3~1") == env.remembered_git_head
        assert env.git_branches() == {"main", "groupy-1", "groupy-3"}
        assert env.git_tags() == {"groupy/groupy-1/init", "groupy/groupy-3/init"}


class Env(TestEnv):
    pass
