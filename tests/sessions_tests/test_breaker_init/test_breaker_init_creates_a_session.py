from sessions_tests.breaker_test_env import Context, TestEnv

NODE_FILES = {
    "src/package-node.breaker.yaml",
    "src/myapp/package-node.breaker.yaml",
    "src/myapp/__init__.py.breaker.yaml",
    "src/myapp/books.py.breaker.yaml",
    "src/myapp/chapters/package-node.breaker.yaml",
    "src/myapp/chapters/__init__.py.breaker.yaml",
    "src/myapp/chapters/create_chapter.py.breaker.yaml",
}


def create_env(context: Context):
    return Env(context)


def test_breaker_init_creates_a_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a git repo with the myapp package in the src dir.
    #
    # The working tree should be clean and there should be no breaker files.
    if env.step(
        env.create_repo_with_target_code(),
        env.remember_git_head(),
    ):
        assert env.git_branch() == "main"
        assert env.git_status() == ""
        assert not env.file_exists(".breaker/session.yaml")
        assert env.node_file_paths() == set()

    # We run breaker init with the src dir as the target dir and a branch name.
    #
    # Breaker should have created the branch and committed the session file,
    # the config file, the group file and the node files on it.
    if env.step(
        env.run_breaker("init", "--target-dir=src", "--branch-name=refactor-myapp"),
    ):
        assert env.git_branch() == "refactor-myapp"
        assert env.git_head() != env.remembered_git_head
        assert env.git_status() == ""
        assert env.files_in_head_commit() == {
            ".breaker/session.yaml",
            ".breaker/config.yaml",
            ".breaker/groups.txt",
            *NODE_FILES,
        }

    # We look at the session.
    #
    # The next stage should be identify-helper-functions, and the target code
    # should be in the src dir.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "identify-helper-functions"
        assert env.session.target_dir == "src"

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
