from create_package_node_file_tests.package_node_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_create_package_node_file_for_the_target_dir(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a source root with a module directly in it, and the myapp
    # package.
    if env.step(
        env.write_file("manage.py", "import myapp\n"),
        env.write_file("myapp/__init__.py"),
        env.write_file("myapp/books.py", "MAX_CHAPTERS = 10\n"),
    ):
        pass

    # We create the package node file for the source root, which is the root
    # package.
    #
    # The node file should be created in the source root. Its name should be
    # "." and it should only list the modules that are directly in the source
    # root.
    if env.step(
        env.create_package_node_file("."),
        env.load_package_node("."),
    ):
        assert env.file_exists("package-node.groupy.yaml")
        assert env.package_node.name == "."
        assert env.package_node.module_names == ["manage.py"]


class Env(TestEnv):
    pass
