from package_nodes_tests.package_node_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_create_package_node_file_only_lists_modules(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the myapp package with an __init__.py and one other module, next
    # to a sub-package, a module node file, a compiled module and a data file.
    if env.step(
        env.write_file("myapp/__init__.py", "VERSION = '1.0'\n"),
        env.write_file("myapp/books.py", "MAX_CHAPTERS = 10\n"),
        env.write_file("myapp/books.py.groupy.yaml", "module_node: {}\n"),
        env.write_file("myapp/__pycache__/books.cpython-310.pyc"),
        env.write_file("myapp/chapters/__init__.py"),
        env.write_file("myapp/chapters/create_chapter.py"),
        env.write_file("myapp/templates/book.html", "<h1>Book</h1>\n"),
    ):
        pass

    # We create the package node file for myapp.
    #
    # It should only list the __init__ and books modules.
    if env.step(
        env.create_package_node_file("myapp"),
        env.load_package_node("myapp"),
    ):
        # An __init__.py is just another module. A sub-package has its own
        # package node file.
        assert env.package_node.module_names == [
            "myapp/__init__.py",
            "myapp/books.py",
        ]


class Env(TestEnv):
    pass
