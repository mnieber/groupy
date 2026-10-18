from groupy_sync_tests.groupy_sync_test_env import Context, TestEnv

BOOKS_PY = """\
def create_book(title):
    return _normalize_title(title)


def _normalize_title(title):
    return _strip(title)


def _strip(title):
    return title.strip()
"""

# books.py after create_book and _normalize_title were replaced by make_book.
NEW_BOOKS_PY = """\
def make_book(title):
    return _strip(title)


def _strip(title):
    return title.strip()
"""


def create_env(context: Context):
    return Env(context)


def test_groupy_sync_removes_a_function_and_its_helper(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, where books.py has a chain of
    # helper functions. In the node file, _strip is a helper of
    # _normalize_title, which is a helper of create_book, and _strip has a
    # responsibility.
    if env.step(
        env.create_repo_with_target_code(),
        env.write_file("src/myapp/books.py", BOOKS_PY),
        env.commit_all("add books"),
        env.run_groupy("init", "--target-dir=src"),
        env.move_function_to_parent("myapp/books.py", "_strip", "_normalize_title"),
        env.move_function_to_parent(
            "myapp/books.py", "_normalize_title", "create_book"
        ),
        env.add_responsibility(
            "myapp/books.py", "create_book._normalize_title._strip", "Strips the title"
        ),
        env.commit_all("nest the helpers"),
    ):
        pass

    # We remove create_book and its helper _normalize_title from the source,
    # and run groupy sync.
    #
    # Both nodes should be reported as removed.
    if env.step(
        env.write_file("src/myapp/books.py", NEW_BOOKS_PY),
        env.run_groupy_sync(),
    ):
        assert env.output_lines == [
            "myapp/books.py: removed _normalize_title (it had helper_function_nodes)",
            "myapp/books.py: removed create_book (it had helper_function_nodes)",
            "myapp/books.py: added make_book",
            "Please review the changes to the node files (e.g. with git diff), "
            "and move the analysis of renamed nodes.",
        ]

    # We look at the node file.
    #
    # _strip should have taken the place of the removed nodes, once, with its
    # own analysis.
    if env.step(
        env.load_module_node("myapp/books.py"),
    ):
        assert env.names(env.module_node.function_nodes) == ["make_book", "_strip"]
        assert env.function_node("_strip").responsibilities == ["Strips the title"]
        assert env.function_node("_strip").helper_function_nodes == []


class Env(TestEnv):
    pass
