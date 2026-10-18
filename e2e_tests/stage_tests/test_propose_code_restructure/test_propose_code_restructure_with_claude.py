from stage_tests.e2e_test_env import Context, TestEnv

from groupy.package_nodes.actions.set_proposed_module import set_proposed_module

BOOKS = "myapp/books.py"

BOOKS_PY = """\
from dataclasses import dataclass


@dataclass
class Book:
    title: str
    isbn: str


def is_valid_isbn(isbn):
    return len(isbn.replace("-", "")) == 13


def create_book(books, title, isbn):
    if not is_valid_isbn(isbn):
        raise ValueError(f"Invalid ISBN: {isbn}")
    book = Book(title=title, isbn=isbn)
    books.append(book)
    return book
"""


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is
    # propose-code-restructure. The module books.py has a model (Book), a
    # rule (is_valid_isbn) and an action (create_book), and the proposed
    # modules have a package myapp/books.
    if env.step(
        env.create_session_with_claude({BOOKS: BOOKS_PY}),
        env.edit_package_node_file(
            set_proposed_module, "myapp/books", "The books of the library"
        ),
        env.set_next_stage("propose-code-restructure"),
    ):
        pass

    # We run groupy next.
    #
    # Claude should have proposed a code restructure without problems, so
    # that the stage finished with a clean working tree.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "apply-code-restructure"
        assert env.git_status() == ""

    # We look at the node file of books.py.
    #
    # Claude should have recognized the model, the rule and the action, and
    # moved them to myapp/books.
    if env.step(
        env.load_module_node(BOOKS),
    ):
        assert env.class_node("Book").code_unit_type == "model"
        assert env.function_node("is_valid_isbn").code_unit_type == "rule"
        assert env.function_node("create_book").code_unit_type == "action"
        for node in [
            env.class_node("Book"),
            env.function_node("is_valid_isbn"),
            env.function_node("create_book"),
        ]:
            assert node.move_to_file.startswith("myapp/books/"), node.name


class Env(TestEnv):
    pass
