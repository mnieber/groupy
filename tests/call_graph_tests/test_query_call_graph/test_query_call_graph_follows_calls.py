import typing as T

from breaker.call_graph.models.call_edge import CallEdge
from breaker.call_graph.rules.get_callees import get_callees
from breaker.call_graph.rules.get_callers import get_callers
from breaker.functions.rules.get_source import get_source
from call_graph_tests.call_graph_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_query_call_graph_follows_calls(context: Context):
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

    # We get the callers of capitalize.
    #
    # They should be the edges that end in capitalize.
    if env.step(
        env.get_callers("myapp/titles.py:capitalize"),
    ):
        assert {edge.caller for edge in env.edges} == {
            "myapp/titles.py:format_title",
            "myapp/authors.py:Author.__init__",
        }

    # We get the callees of create_book.
    #
    # They should be the edges that start in create_book.
    if env.step(
        env.get_callees("myapp/books.py:create_book"),
    ):
        assert {edge.callee for edge in env.edges} == {
            "myapp/titles.py:format_title",
            "myapp/books.py:Book.__init__",
        }

    # We get the source of the save method of Book.
    #
    # It should be the source of the method, without the indentation of the
    # class body.
    if env.step(
        env.get_source("myapp/books.py:Book.save"),
    ):
        assert env.source == "def save(self):\n    self._validate()\n"


class Env(TestEnv):
    def __post_init__(self):
        self.edges: T.List[CallEdge] = None
        self.source: str = None

    def get_callers(self, location: str) -> None:
        self.edges = get_callers(self.call_graph, location)

    def get_callees(self, location: str) -> None:
        self.edges = get_callees(self.call_graph, location)

    def get_source(self, location: str) -> None:
        self.source = get_source(self.source_root, location)
