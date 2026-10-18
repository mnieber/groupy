from sessions_tests.groupy_test_env import Context, TestEnv

from groupy.sessions.utils.exceptions import DirtyWorkingTreeError


def create_env(context: Context):
    return Env(context)


def test_groupy_init_requires_a_clean_working_tree(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package, and we change a tracked file
    # without committing it.
    if env.step(
        env.create_repo_with_target_code(),
        env.append_to_file("src/myapp/books.py", "\nDEFAULT_TITLE = 'Untitled'\n"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy init.
    #
    # It should raise a DirtyWorkingTreeError and leave the repo untouched.
    if env.step(
        env.run_groupy_and_catch_error("init", "--accept-risks", "--target-dir=src"),
    ):
        assert isinstance(env.error, DirtyWorkingTreeError)
        assert env.git_branch() == "main"
        assert env.git_branches() == {"main"}
        assert env.git_head() == env.remembered_git_head
        assert not env.file_exists(".groupy/session.yaml")
        assert env.node_file_paths() == set()

    # We commit the change, but add an untracked file.
    if env.step(
        env.commit_all("add default title"),
        env.write_file("src/myapp/authors.py", "AUTHORS = []\n"),
    ):
        pass

    # We run groupy init again.
    #
    # An untracked file also makes the working tree unclean, so it should
    # raise a DirtyWorkingTreeError again.
    if env.step(
        env.run_groupy_and_catch_error("init", "--accept-risks", "--target-dir=src"),
    ):
        assert isinstance(env.error, DirtyWorkingTreeError)
        assert env.git_branches() == {"main"}
        assert not env.file_exists(".groupy/session.yaml")


class Env(TestEnv):
    pass
