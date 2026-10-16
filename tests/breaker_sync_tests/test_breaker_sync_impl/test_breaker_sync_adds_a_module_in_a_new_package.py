from breaker_sync_tests.breaker_sync_test_env import Context, TestEnv

CREATE_AUTHOR_PY = """\
def create_author(name):
    return {"name": name}
"""


def create_env(context: Context):
    return Env(context)


def test_breaker_sync_adds_a_module_in_a_new_package(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, and we add the module
    # create_author.py in the new (namespace) package myapp/authors.
    if env.step(
        env.create_session(),
        env.write_file("src/myapp/authors/create_author.py", CREATE_AUTHOR_PY),
    ):
        pass

    # We run breaker sync.
    #
    # It should create the node file of the module.
    if env.step(
        env.run_breaker_sync(),
    ):
        assert env.output_lines == [
            "myapp/authors/create_author.py: created the node file",
            "Please review the changes to the node files (e.g. with git diff), "
            "and move the analysis of renamed nodes.",
        ]
        assert env.file_exists("src/myapp/authors/create_author.py.breaker.yaml")

    # We look at the package node file of the new package.
    #
    # It should have been created, and list the new module.
    if env.step(
        env.load_package_node("myapp/authors"),
    ):
        assert env.package_node.module_names == ["myapp/authors/create_author.py"]

    # We look at the group file.
    #
    # No other module is in the dir of the new module, so it should be in a new
    # group, after the existing groups.
    if env.step(
        env.load_groups(),
    ):
        assert env.module_names_per_group() == [
            ["myapp/__init__.py", "myapp/books.py"],
            ["myapp/chapters/__init__.py", "myapp/chapters/create_chapter.py"],
            ["myapp/authors/create_author.py"],
        ]


class Env(TestEnv):
    pass
