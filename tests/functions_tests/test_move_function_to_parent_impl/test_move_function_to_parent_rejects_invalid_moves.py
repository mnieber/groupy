from functions_tests.functions_test_env import Context, TestEnv

from groupy.functions.actions.move_function_to_parent import InvalidParentError
from groupy.nodes.utils.exceptions import NodeNotFoundError

BOOKS_PY = """\
def create_book(title):
    return Book(normalize_title(title))


def normalize_title(title):
    return strip_quotes(title).strip()


def strip_quotes(title):
    return title.strip('"')


class Book:
    def __init__(self, title):
        self.title = title
"""


def create_env(context: Context):
    return Env(context)


def test_move_function_to_parent_rejects_invalid_moves(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file, in which
    # strip_quotes is a helper function of normalize_title.
    if env.step(
        env.write_module("myapp/books.py", BOOKS_PY),
        env.create_module_node_file("myapp/books.py"),
        env.move_function_to_parent(
            "myapp/books.py", "strip_quotes", "normalize_title"
        ),
        env.remember_node_file("myapp/books.py"),
    ):
        pass

    # We move a function that does not exist.
    #
    # It should raise a NodeNotFoundError and leave the node file unchanged.
    if env.step(
        env.move_function_to_parent_and_catch_error(
            "myapp/books.py", "get_title", "create_book"
        ),
    ):
        assert isinstance(env.error, NodeNotFoundError)
        assert env.read_file("myapp/books.py.groupy.yaml") == (
            env.remembered_node_file_text
        )

    # We move a function to a parent that does not exist, and to a method of
    # a class that does not have that method.
    #
    # Both should raise a NodeNotFoundError.
    if env.step(
        env.move_function_to_parent_and_catch_error(
            "myapp/books.py", "normalize_title", "create_novel"
        ),
    ):
        assert isinstance(env.error, NodeNotFoundError)

    if env.step(
        env.move_function_to_parent_and_catch_error(
            "myapp/books.py", "normalize_title", "Book.add_chapter"
        ),
    ):
        assert isinstance(env.error, NodeNotFoundError)

    # We move normalize_title to itself, and to its own helper function
    # strip_quotes.
    #
    # Both should raise an InvalidParentError, because a function cannot be
    # its own helper function.
    if env.step(
        env.move_function_to_parent_and_catch_error(
            "myapp/books.py", "normalize_title", "normalize_title"
        ),
    ):
        assert isinstance(env.error, InvalidParentError)

    if env.step(
        env.move_function_to_parent_and_catch_error(
            "myapp/books.py", "normalize_title", "normalize_title.strip_quotes"
        ),
    ):
        assert isinstance(env.error, InvalidParentError)
        assert env.read_file("myapp/books.py.groupy.yaml") == (
            env.remembered_node_file_text
        )


class Env(TestEnv):
    pass
