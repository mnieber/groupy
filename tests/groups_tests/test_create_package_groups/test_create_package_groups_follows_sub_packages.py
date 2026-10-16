from groups_tests.groups_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_create_package_groups_follows_sub_packages(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have modules in the root package myapp, in its sub-packages books and
    # authors, and in the forms package inside books. The authors and forms
    # packages are namespace packages (without an __init__.py).
    if env.step(
        env.add_modules(
            {
                "myapp/__init__.py": 0,
                "myapp/settings.py": 10,
                "myapp/books/__init__.py": 0,
                "myapp/books/create_book.py": 30,
                "myapp/books/forms/book_form.py": 20,
                "myapp/authors/create_author.py": 30,
            }
        ),
    ):
        pass

    # We create package groups.
    #
    # Each sub-package of myapp should be a group, which includes the modules
    # of its own sub-packages. The modules that are directly in myapp should
    # form a group of their own. The groups should be numbered in the order
    # of their first module path.
    if env.step(
        env.create_package_groups(),
    ):
        assert env.group_nrs() == [1, 2, 3]
        assert env.module_names_per_group() == [
            ["myapp/__init__.py", "myapp/settings.py"],
            ["myapp/authors/create_author.py"],
            [
                "myapp/books/__init__.py",
                "myapp/books/create_book.py",
                "myapp/books/forms/book_form.py",
            ],
        ]


class Env(TestEnv):
    pass
