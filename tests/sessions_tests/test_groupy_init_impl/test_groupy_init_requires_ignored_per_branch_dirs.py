from sessions_tests.groupy_test_env import Context, TestEnv

from groupy.sessions.utils.exceptions import BranchDirsNotIgnoredError


def create_env(context: Context):
    return Env(context)


def test_groupy_init_requires_ignored_per_branch_dirs(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, but the .gitignore doesn't
    # ignore the per-branch dirs.
    if env.step(
        env.create_repo_with_target_code(),
        env.write_file(".gitignore", "*.pyc\n"),
        env.commit_all("ignore bytecode"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy init.
    #
    # It should raise a BranchDirsNotIgnoredError and leave the repo untouched.
    if env.step(
        env.run_groupy_and_catch_error("init", "--accept-risks", "--target-dir=src"),
    ):
        assert isinstance(env.error, BranchDirsNotIgnoredError)
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main"}
        assert env.git_head() == env.remembered_git_head
        assert not env.file_exists(".groupy/session.yaml")

    # We ignore the per-branch dirs, and run groupy init again.
    if env.step(
        env.write_file(".gitignore", "*.pyc\n/.groupy/*/\n"),
        env.commit_all("ignore the per-branch dirs"),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        assert env.git_branch() == "groupy-1"
        assert env.git_status() == ""


class Env(TestEnv):
    pass
