from functions_tests.functions_test_env import Context, TestEnv

BOOKS_PY = """\
def create_book(title):
    title = normalize_title(title)
    _validate_title(title)
    return Book(title)


def normalize_title(title):
    return strip_quotes(title).strip()


def strip_quotes(title):
    return title.strip('"')


def _validate_title(title):
    if not title:
        raise ValueError("A book needs a title")


class Book:
    def __init__(self, title):
        self.title = title

    def add_chapter(self, title):
        return {"title": format_chapter_title(title)}


def format_chapter_title(title):
    return title.title()


def get_title_length(book):
    return len(book.title)
"""


def create_env(context: Context):
    return Env(context)


def test_move_function_to_parent_nests_helper_functions(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file.
    #
    # All functions should be top-level function nodes.
    if env.step(
        env.write_module("myapp/books.py", BOOKS_PY),
        env.create_module_node_file("myapp/books.py"),
        env.load_module_node("myapp/books.py"),
    ):
        assert env.names(env.module_node.function_nodes) == [
            "create_book",
            "normalize_title",
            "strip_quotes",
            "_validate_title",
            "format_chapter_title",
            "get_title_length",
        ]

    # We move _validate_title to create_book.
    #
    # _validate_title should become a helper function node of create_book.
    if env.step(
        env.move_function_to_parent("myapp/books.py", "_validate_title", "create_book"),
        env.load_module_node("myapp/books.py"),
    ):
        assert "_validate_title" not in env.names(env.module_node.function_nodes)
        assert env.names(env.function_node("create_book").helper_function_nodes) == [
            "_validate_title"
        ]

    # We move strip_quotes to normalize_title, and then normalize_title to
    # create_book.
    #
    # normalize_title should be added after the existing helper function node
    # of create_book, and it should keep strip_quotes as its own helper.
    if env.step(
        env.move_function_to_parent(
            "myapp/books.py", "strip_quotes", "normalize_title"
        ),
        env.move_function_to_parent("myapp/books.py", "normalize_title", "create_book"),
        env.load_module_node("myapp/books.py"),
    ):
        create_book_node = env.function_node("create_book")
        assert env.names(create_book_node.helper_function_nodes) == [
            "_validate_title",
            "normalize_title",
        ]
        normalize_title_node = create_book_node.helper_function_nodes[1]
        assert env.names(normalize_title_node.helper_function_nodes) == ["strip_quotes"]

    # We move format_chapter_title to the add_chapter method of Book.
    #
    # format_chapter_title should become a helper function node of the
    # add_chapter method node.
    if env.step(
        env.move_function_to_parent(
            "myapp/books.py", "format_chapter_title", "Book.add_chapter"
        ),
        env.load_module_node("myapp/books.py"),
    ):
        add_chapter_node = env.class_node("Book").method_nodes[1]
        assert add_chapter_node.name == "add_chapter"
        assert env.names(add_chapter_node.helper_function_nodes) == [
            "format_chapter_title"
        ]

    # We look at the result.
    #
    # Only the functions that are not helper functions should be top-level
    # function nodes, and the module should be unchanged.
    if env.step():
        assert env.names(env.module_node.function_nodes) == [
            "create_book",
            "get_title_length",
        ]
        # The move only changes the node file. In the module, the helper
        # functions stay top-level functions and keep their names.
        assert env.read_file("myapp/books.py") == BOOKS_PY


class Env(TestEnv):
    pass
