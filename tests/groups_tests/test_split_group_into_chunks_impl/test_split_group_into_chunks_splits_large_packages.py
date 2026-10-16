from groups_tests.groups_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_split_group_into_chunks_splits_large_packages(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the myapp package (10 lines), the books package with five
    # modules of 30 lines (150 lines), and the forms package (10 lines).
    module_sizes = {
        "myapp/__init__.py": 10,
        "myapp/books/a.py": 30,
        "myapp/books/b.py": 30,
        "myapp/books/c.py": 30,
        "myapp/books/d.py": 30,
        "myapp/books/e.py": 30,
        "myapp/books/forms/f.py": 10,
    }
    if env.step(
        env.add_modules(module_sizes),
    ):
        pass

    # We split a group with these modules into chunks of at most 70 lines.
    #
    # The books package does not fit in a chunk, so it should start a new
    # chunk and be split by sorted path. The forms package fits in the last
    # chunk of the books package.
    if env.step(
        env.split_group_into_chunks(sorted(module_sizes), max_chunk_lines=70),
    ):
        assert env.module_names_per_chunk() == {
            "group-1/chunk-1": ["myapp/__init__.py"],
            "group-1/chunk-2": ["myapp/books/a.py", "myapp/books/b.py"],
            "group-1/chunk-3": ["myapp/books/c.py", "myapp/books/d.py"],
            "group-1/chunk-4": ["myapp/books/e.py", "myapp/books/forms/f.py"],
        }


def test_split_group_into_chunks_gives_a_large_module_its_own_chunk(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have the module books.py of 200 lines between two small modules.
    module_sizes = {
        "myapp/authors.py": 20,
        "myapp/books.py": 200,
        "myapp/chapters.py": 20,
    }
    if env.step(
        env.add_modules(module_sizes),
    ):
        pass

    # We split a group with these modules into chunks of at most 70 lines.
    #
    # The module of 200 lines should get a chunk of its own.
    if env.step(
        env.split_group_into_chunks(sorted(module_sizes), max_chunk_lines=70),
    ):
        assert env.module_names_per_chunk() == {
            "group-1/chunk-1": ["myapp/authors.py"],
            "group-1/chunk-2": ["myapp/books.py"],
            "group-1/chunk-3": ["myapp/chapters.py"],
        }


class Env(TestEnv):
    pass
