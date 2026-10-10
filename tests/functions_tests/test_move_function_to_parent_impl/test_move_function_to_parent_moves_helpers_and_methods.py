from functions_tests.functions_test_env import Context, TestEnv

BOOKS_PY = """\
def create_book(title):
    return Book(normalize_title(title))


def create_novel(title):
    return Book(normalize_title(title))


def normalize_title(title):
    return title.strip()


class Book:
    def __init__(self, title):
        self.title = title

    def save(self):
        self._validate()

    def _validate(self):
        assert self.title
"""


def create_env(context: Context):
    return Env(context)


def test_move_function_to_parent_moves_helpers_and_methods(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file, in which
    # normalize_title is a helper function of create_book.
    #
    # The move does not check who calls normalize_title (it is also called by
    # create_novel); that is up to the caller of the action.
    if env.step(
        env.write_module("myapp/books.py", BOOKS_PY),
        env.create_module_node_file("myapp/books.py"),
        env.move_function_to_parent("myapp/books.py", "normalize_title", "create_book"),
        env.load_module_node("myapp/books.py"),
    ):
        assert env.names(env.function_node("create_book").helper_function_nodes) == [
            "normalize_title"
        ]

    # We move the helper function normalize_title from create_book to
    # create_novel.
    #
    # It should no longer be a helper function node of create_book, but of
    # create_novel.
    if env.step(
        env.move_function_to_parent(
            "myapp/books.py", "create_book.normalize_title", "create_novel"
        ),
        env.load_module_node("myapp/books.py"),
    ):
        assert env.function_node("create_book").helper_function_nodes == []
        assert env.names(env.function_node("create_novel").helper_function_nodes) == [
            "normalize_title"
        ]

    # We move the _validate method of Book to the save method.
    #
    # _validate should no longer be a method node of Book, but a helper
    # function node of save.
    if env.step(
        env.move_function_to_parent("myapp/books.py", "Book._validate", "Book.save"),
        env.load_module_node("myapp/books.py"),
    ):
        book_node = env.class_node("Book")
        assert env.names(book_node.method_nodes) == ["__init__", "save"]
        assert env.names(book_node.method_nodes[1].helper_function_nodes) == [
            "_validate"
        ]

    # We move the save method of Book to create_book.
    #
    # save should become a helper function node of create_book, and it should
    # keep _validate as its own helper function node.
    if env.step(
        env.move_function_to_parent("myapp/books.py", "Book.save", "create_book"),
        env.load_module_node("myapp/books.py"),
    ):
        assert env.names(env.class_node("Book").method_nodes) == ["__init__"]
        create_book_node = env.function_node("create_book")
        assert env.names(create_book_node.helper_function_nodes) == ["save"]
        assert env.names(
            create_book_node.helper_function_nodes[0].helper_function_nodes
        ) == ["_validate"]
        # The move only changes the node file.
        assert env.read_file("myapp/books.py") == BOOKS_PY


class Env(TestEnv):
    pass
