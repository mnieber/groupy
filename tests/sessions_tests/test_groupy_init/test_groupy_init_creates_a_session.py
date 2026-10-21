from sessions_tests.groupy_test_env import Context, TestEnv

NODE_FILES = {
    "src/package-node.groupy.yaml",
    "src/myapp/package-node.groupy.yaml",
    "src/myapp/__init__.py.groupy.yaml",
    "src/myapp/books.py.groupy.yaml",
    "src/myapp/chapters/package-node.groupy.yaml",
    "src/myapp/chapters/__init__.py.groupy.yaml",
    "src/myapp/chapters/create_chapter.py.groupy.yaml",
}


def create_env(context: Context):
    return Env(context)


def test_groupy_init_creates_a_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package in the src dir.
    #
    # The working tree should be clean and there should be no groupy files.
    if env.step(
        env.create_repo_with_target_code(),
        env.remember_git_head(),
    ):
        assert env.git_branch() == "main"
        assert env.git_status() == ""
        assert not env.file_exists(".groupy/session.yaml")
        assert env.node_file_paths() == set()

    # We run groupy init with the src dir as the target dir and a branch name.
    #
    # Groupy should have created the branch and committed the session file,
    # the config file and the node files on it, and tagged the commit. The
    # group file is created by the first stage.
    if env.step(
        env.run_groupy(
            "init", "--accept-risks", "--target-dir=src", "--branch-name=refactor-myapp"
        ),
    ):
        assert env.git_branch() == "refactor-myapp"
        assert env.git_head() != env.remembered_git_head
        assert env.git_status() == ""
        assert env.files_in_head_commit() == {
            ".groupy/session.yaml",
            ".groupy/config.yaml",
            *NODE_FILES,
        }
        assert env.git_tags() == {"groupy/refactor-myapp/init"}

    # We look at the session.
    #
    # The next stage should be group-modules, the target code should be in
    # the src dir, and the base branch should be main.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "group-modules"
        assert env.session.target_dir == "src"
        assert env.session.base_branch == "main"

    # We look at the per-branch dir.
    #
    # Groupy should have created .groupy/refactor-myapp, for the files that it
    # doesn't commit (e.g. the logs of Claude). All dirs in .groupy should be
    # excluded from git.
    if env.step():
        assert env.file_exists(".groupy/refactor-myapp")
        assert "/.groupy/*/" in env.git_ignores()

    # We look at the node files.
    #
    # There should be a package node file per package (including the target
    # dir, which is the root package) and a module node file per module.
    if env.step():
        # An __init__.py is just another module, so it also has a module node
        # file.
        assert env.node_file_paths() == NODE_FILES


class Env(TestEnv):
    pass
