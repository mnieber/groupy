from create_package_node_file_tests.package_node_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_create_package_node_file_reflects_the_package(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a source root with the myapp package, which has two modules and
    # the chapters sub-package.
    #
    # There should be no package node files.
    if env.step(
        env.write_file("myapp/__init__.py"),
        env.write_file("myapp/books.py", "MAX_CHAPTERS = 10\n"),
        env.write_file("myapp/authors.py", "AUTHORS = []\n"),
        env.write_file("myapp/chapters/__init__.py"),
        env.write_file("myapp/chapters/create_chapter.py", "TITLE = 'Intro'\n"),
    ):
        assert not env.file_exists("myapp/package-node.breaker.yaml")
        assert not env.file_exists("myapp/chapters/package-node.breaker.yaml")

    # We create the package node file for myapp.
    #
    # The node file should be created in the package root. It should name the
    # package by its path relative to the source root, and list its modules.
    if env.step(
        env.create_package_node_file("myapp"),
        env.load_package_node("myapp"),
    ):
        assert env.file_exists("myapp/package-node.breaker.yaml")
        assert env.package_node.name == "myapp"
        # Like all paths in node files, the module names are relative to the
        # source root. They are sorted, so that the node file is stable.
        assert env.package_node.module_names == [
            "myapp/__init__.py",
            "myapp/authors.py",
            "myapp/books.py",
        ]
        # Modules are proposed in the propose-module-layout stage.
        assert env.package_node.proposed_modules == {}

    # We create the package node file for the chapters sub-package.
    #
    # It should list the modules of the sub-package.
    if env.step(
        env.create_package_node_file("myapp/chapters"),
        env.load_package_node("myapp/chapters"),
    ):
        assert env.file_exists("myapp/chapters/package-node.breaker.yaml")
        assert env.package_node.name == "myapp/chapters"
        assert env.package_node.module_names == [
            "myapp/chapters/__init__.py",
            "myapp/chapters/create_chapter.py",
        ]


class Env(TestEnv):
    pass
