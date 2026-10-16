from groups_tests.groups_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_create_package_groups_for_several_top_level_packages(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the top-level packages myapp and tools. The myapp package only
    # contains the books sub-package (it has no modules of its own). The tools
    # package has a module of its own and the lint sub-package.
    if env.step(
        env.add_modules(
            {
                "myapp/books/create_book.py": 30,
                "tools/__init__.py": 0,
                "tools/lint/check.py": 20,
            }
        ),
    ):
        pass

    # We create package groups.
    #
    # Every top-level package should be split into its sub-packages, and a
    # top-level package without modules of its own should not get a group.
    if env.step(
        env.create_package_groups(),
    ):
        assert env.module_names_per_group() == [
            ["myapp/books/create_book.py"],
            ["tools/__init__.py"],
            ["tools/lint/check.py"],
        ]


class Env(TestEnv):
    pass
