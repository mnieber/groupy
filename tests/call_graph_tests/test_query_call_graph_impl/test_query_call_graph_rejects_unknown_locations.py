from call_graph_tests.call_graph_test_env import Context, TestEnv

from groupy.call_graph.rules.get_callers import get_callers
from groupy.functions.rules.get_source import get_source
from groupy.nodes.utils.exceptions import NodeNotFoundError


def create_env(context: Context):
    return Env(context)


def test_query_call_graph_rejects_unknown_locations(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the modules myapp/titles.py, myapp/books.py and myapp/authors.py,
    # and their call graph.
    if env.step(
        env.write_myapp_modules(),
        env.build_call_graph(),
        env.load_call_graph(),
    ):
        pass

    # We get the callers of a function that does not exist.
    #
    # It should raise a NodeNotFoundError, rather than return no callers.
    if env.step(
        env.get_callers_and_catch_error("myapp/titles.py:normalize"),
    ):
        assert isinstance(env.error, NodeNotFoundError)

    # We get the source of a method that does not exist, and of a function in
    # a module that does not exist.
    #
    # Each should raise a NodeNotFoundError.
    if env.step(
        env.get_source_and_catch_error("myapp/books.py:Book.publish"),
    ):
        assert isinstance(env.error, NodeNotFoundError)

    if env.step(
        env.get_source_and_catch_error("myapp/novels.py:create_novel"),
    ):
        assert isinstance(env.error, NodeNotFoundError)

    # We get the callers of create_book, which exists but is not called.
    #
    # It should return no callers.
    if env.step(
        env.get_callers_and_catch_error("myapp/books.py:create_book"),
    ):
        assert env.error is None
        assert env.edges == []


class Env(TestEnv):
    def __post_init__(self):
        self.edges = None

    def get_callers_and_catch_error(self, location: str) -> None:
        self.error = None
        try:
            self.edges = get_callers(self.call_graph, location)
        except Exception as error:
            self.error = error

    def get_source_and_catch_error(self, location: str) -> None:
        self.error = None
        try:
            get_source(self.source_root, location)
        except Exception as error:
            self.error = error
