from create_module_node_file_tests.module_node_test_env import Context, TestEnv

BOOKS_PY = """\
import typing as T

from myapp.chapters.create_chapter import create_chapter

MAX_CHAPTERS = 10
DEFAULT_TITLE = "Untitled"


class Book:
    def __init__(self, title):
        self.title = title
        self.chapters = []

    def add_chapter(self, title):
        def _check_capacity():
            if len(self.chapters) >= MAX_CHAPTERS:
                raise TooManyChaptersError()

        _check_capacity()
        self.chapters.append(create_chapter(self, title))


class TooManyChaptersError(Exception):
    pass


def create_book(title: T.Optional[str]) -> Book:
    def _normalize_title(title):
        return title.strip()

    title = _normalize_title(title or DEFAULT_TITLE)
    _validate_title(title)
    return Book(title)


def _validate_title(title):
    if not title:
        raise ValueError("A book needs a title")


def get_title_length(book):
    return len(book.title)
"""


def create_env(context: Context):
    return Env(context)


def test_create_module_node_file_reflects_the_module(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a source root with the module myapp/books.py.
    #
    # There should be no node file for the module.
    if env.step(
        env.write_module("myapp/books.py", BOOKS_PY),
    ):
        assert not env.file_exists("myapp/books.py.groupy.yaml")

    # We create the module node file for myapp/books.py.
    #
    # The node file should be created next to the module. It should name the
    # module by its path relative to the source root, and count its lines.
    if env.step(
        env.create_module_node_file("myapp/books.py"),
        env.load_module_node("myapp/books.py"),
    ):
        assert env.file_exists("myapp/books.py.groupy.yaml")
        assert env.module_node.name == "myapp/books.py"
        assert env.module_node.line_count == len(BOOKS_PY.splitlines())

    # We look at the variable nodes.
    #
    # There should be a variable node per module-level variable, in source
    # order.
    if env.step():
        # Imported names are not variables of the module.
        assert env.names(env.module_node.variable_nodes) == [
            "MAX_CHAPTERS",
            "DEFAULT_TITLE",
        ]

    # We look at the class nodes.
    #
    # There should be a class node per class, with a method node per method.
    # The _check_capacity function that is nested in add_chapter is part
    # of the body of add_chapter, so it has no node.
    if env.step():
        assert env.names(env.module_node.class_nodes) == [
            "Book",
            "TooManyChaptersError",
        ]
        book_node = env.class_node("Book")
        assert env.names(book_node.method_nodes) == ["__init__", "add_chapter"]
        assert book_node.method_nodes[1].helper_function_nodes == []
        assert env.class_node("TooManyChaptersError").method_nodes == []

    # We look at the function nodes.
    #
    # There should be a function node per top-level function, and none of
    # them should have helper function nodes yet (since this stage comes before the
    # identify-helper-functions stage).
    if env.step():
        assert env.names(env.module_node.function_nodes) == [
            "create_book",
            "_validate_title",
            "get_title_length",
        ]
        for function_node in env.module_node.function_nodes:
            assert function_node.helper_function_nodes == []
        # The _normalize_title function that is nested in create_book is part
        # of the body of create_book, so it has no node.
        assert "_normalize_title" not in env.names(env.module_node.function_nodes)

    # We look at the fields that later stages fill in.
    #
    # They should still be empty.
    if env.step():
        assert env.module_node.rename_to is None
        assert env.module_node.concepts == {}
        assert env.module_node.renamings == {}

        function_node = env.function_node("create_book")
        assert function_node.rename_to is None
        assert function_node.move_to_file is None
        assert function_node.code_unit_type is None
        # Helper candidates are marked in the identify-helper-functions stage,
        # when Groupy has computed the call graph.
        assert function_node.is_helper_candidate is False
        assert function_node.concepts == {}
        assert function_node.local_terms == {}
        assert function_node.responsibilities == []
        assert function_node.steps == []

        class_node = env.class_node("Book")
        assert class_node.rename_to is None
        assert class_node.code_unit_type is None
        assert class_node.concepts == {}


class Env(TestEnv):
    pass
