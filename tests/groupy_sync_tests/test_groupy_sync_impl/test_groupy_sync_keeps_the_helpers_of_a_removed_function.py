from groupy_sync_tests.groupy_sync_test_env import Context, TestEnv

# books.py after create_book was renamed to make_book.
BOOKS_PY = """\
MAX_CHAPTERS = 10


class Book:
    def __init__(self, title):
        self.title = title


def make_book(title):
    return Book(_normalize_title(title))


def _normalize_title(title):
    return title.strip()
"""


def create_env(context: Context):
    return Env(context)


def test_groupy_sync_keeps_the_helpers_of_a_removed_function(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package. In the node file,
    # _normalize_title is a helper of create_book, and it has a
    # responsibility.
    if env.step(
        env.create_session(),
        env.move_function_to_parent(
            "myapp/books.py", "_normalize_title", "create_book"
        ),
        env.add_responsibility(
            "myapp/books.py", "create_book._normalize_title", "Strips the title"
        ),
        env.commit_all("nest _normalize_title"),
    ):
        pass

    # We rename create_book to make_book in the source, and run groupy sync.
    #
    # The node of create_book should be removed, and the line should name its
    # helper function nodes.
    if env.step(
        env.write_file("src/myapp/books.py", BOOKS_PY),
        env.run_groupy_sync(),
    ):
        assert env.output_lines == [
            "myapp/books.py: removed create_book (it had helper_function_nodes)",
            "myapp/books.py: added make_book",
            "Please review the changes to the node files (e.g. with git diff), "
            "and move the analysis of renamed nodes.",
        ]

    # We look at the node file.
    #
    # The helper function node should have taken the place of create_book,
    # with its own analysis (the responsibilities of create_book are gone), and
    # make_book should be inserted before it, in source order.
    if env.step(
        env.load_module_node("myapp/books.py"),
    ):
        assert env.names(env.module_node.function_nodes) == [
            "make_book",
            "_normalize_title",
        ]
        assert env.function_node("_normalize_title").responsibilities == [
            "Strips the title"
        ]


class Env(TestEnv):
    pass
