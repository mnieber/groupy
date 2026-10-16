from groups_tests.groups_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_create_simple_groups_divides_modules_by_size(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have six modules with node files, in the root package and in the
    # books sub-package.
    if env.step(
        env.add_modules(
            {
                "myapp/titles.py": 20,
                "myapp/__init__.py": 0,
                "myapp/books/delete_book.py": 50,
                "myapp/authors.py": 40,
                "myapp/books/__init__.py": 0,
                "myapp/books/create_book.py": 30,
            }
        ),
    ):
        pass

    # We create simple groups of at most 80 lines.
    #
    # The modules should be sorted by path, and a group should get modules
    # until the next module would make it larger than 80 lines.
    if env.step(
        env.create_simple_groups(max_group_lines=80),
    ):
        assert env.group_nrs() == [1, 2]
        assert env.module_names_per_group() == [
            [
                "myapp/__init__.py",
                "myapp/authors.py",
                "myapp/books/__init__.py",
                "myapp/books/create_book.py",
            ],
            ["myapp/books/delete_book.py", "myapp/titles.py"],
        ]
        groups = env.module_names_per_group()

    # We create the simple groups again.
    #
    # We should get the same groups.
    if env.step(
        env.create_simple_groups(max_group_lines=80),
    ):
        assert env.module_names_per_group() == groups


class Env(TestEnv):
    pass
