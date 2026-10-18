from groupy_sync_tests.groupy_sync_test_env import Context, TestEnv

AUTHORS_PY = """\
def create_author(name):
    return {"name": name}
"""


def create_env(context: Context):
    return Env(context)


def test_groupy_sync_before_the_modules_are_grouped(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose first stage
    # (group-modules) has not run yet, so there is no group file. We add the
    # module authors.py.
    if env.step(
        env.create_repo_with_target_code(),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
        env.write_file("src/myapp/authors.py", AUTHORS_PY),
    ):
        assert not env.file_exists(".groupy/groups.txt")

    # We run groupy sync.
    #
    # It should create the node file of authors.py, without creating a group
    # file: group-modules will group all the modules that exist then.
    if env.step(
        env.run_groupy_sync(),
    ):
        assert env.output_lines[0] == "myapp/authors.py: created the node file"
        assert env.file_exists("src/myapp/authors.py.groupy.yaml")
        assert not env.file_exists(".groupy/groups.txt")


class Env(TestEnv):
    pass
