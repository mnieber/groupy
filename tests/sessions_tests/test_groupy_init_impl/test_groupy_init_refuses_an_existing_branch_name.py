from sessions_tests.groupy_test_env import Context, TestEnv

from groupy.sessions.actions.init_session import BranchExistsError


def create_env(context: Context):
    return Env(context)


def test_groupy_init_refuses_an_existing_branch_name(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, and a branch feature-x of the
    # developer.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_git("branch", "feature-x"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy init with the branch name feature-x.
    #
    # The branch already exists, so it should raise a BranchExistsError and
    # leave the repo untouched.
    if env.step(
        env.run_groupy_and_catch_error(
            "init", "--accept-risks", "--target-dir=src", "--branch-name=feature-x"
        ),
    ):
        assert isinstance(env.error, BranchExistsError)
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main", "feature-x"}
        assert env.git_head() == env.remembered_git_head
        assert env.git_tags() == set()
        assert not env.file_exists(".groupy")

    # We run groupy init with the branch name refactor-myapp, go back to main,
    # and delete the branch (as groupy abort will do, it keeps the per-branch
    # dir).
    if env.step(
        env.run_groupy(
            "init", "--accept-risks", "--target-dir=src", "--branch-name=refactor-myapp"
        ),
        env.run_git("checkout", "main"),
        env.run_git("branch", "-D", "refactor-myapp"),
        env.run_git("tag", "-d", "groupy/refactor-myapp/init"),
    ):
        assert env.git_branches() == {"main", "feature-x"}
        assert env.file_exists(".groupy/refactor-myapp")

    # We run groupy init with the branch name refactor-myapp again.
    #
    # The branch no longer exists, but its per-branch dir does, so it should
    # raise a BranchExistsError again: groupy never reuses a branch name.
    if env.step(
        env.run_groupy_and_catch_error(
            "init", "--accept-risks", "--target-dir=src", "--branch-name=refactor-myapp"
        ),
    ):
        assert isinstance(env.error, BranchExistsError)
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main", "feature-x"}
        assert env.git_head() == env.remembered_git_head


class Env(TestEnv):
    pass
