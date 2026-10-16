from groups_tests.groups_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_create_simple_groups_handles_large_modules(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a module of exactly 50 lines, a module of 200 lines and two small
    # modules.
    if env.step(
        env.add_modules(
            {
                "myapp/authors.py": 50,
                "myapp/books.py": 200,
                "myapp/chapters.py": 10,
                "myapp/titles.py": 10,
            }
        ),
    ):
        pass

    # We create simple groups of at most 50 lines.
    #
    # A module of exactly 50 lines should fit in a group, and the module of 200
    # lines should get a group of its own.
    if env.step(
        env.create_simple_groups(max_group_lines=50),
    ):
        assert env.module_names_per_group() == [
            ["myapp/authors.py"],
            ["myapp/books.py"],
            ["myapp/chapters.py", "myapp/titles.py"],
        ]


def test_create_simple_groups_only_groups_module_node_files(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have two modules with node files, a module without a node file, and
    # the package node file of myapp.
    if env.step(
        env.add_modules({"myapp/authors.py": 10, "myapp/books.py": 10}),
        env.write_module("myapp/scratch.py", 10),
        env.create_package_node_file("myapp"),
    ):
        pass

    # We create simple groups.
    #
    # Only the modules with a node file should be grouped.
    if env.step(
        env.create_simple_groups(max_group_lines=100),
    ):
        assert env.module_names_per_group() == [
            ["myapp/authors.py", "myapp/books.py"],
        ]


class Env(TestEnv):
    pass
