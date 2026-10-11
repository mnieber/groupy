import typing as T

from breaker.call_graph.enums import CallScopes
from breaker.call_graph.models.call_graph_view import CallGraphView, FunctionView
from breaker.call_graph.rules.get_call_graph_view import get_call_graph_view
from breaker.functions.actions.add_responsibility import add_responsibility
from breaker.nodes.actions.create_module_node_file import create_module_node_file
from call_graph_tests.call_graph_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_get_call_graph_view_labels_callers_and_callees(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the modules myapp/titles.py, myapp/books.py and myapp/authors.py,
    # and their call graph. The node file of authors.py has a responsibility
    # for Author.__init__ and for publish.
    if env.step(
        env.write_myapp_modules(),
        env.create_module_node_file("myapp/authors.py"),
        env.add_responsibility(
            "myapp/authors.py", "Author.__init__", "Creates an author"
        ),
        env.add_responsibility(
            "myapp/authors.py", "publish", "Publishes a book or an author"
        ),
        env.add_responsibility("myapp/authors.py", "publish", "Logs the publication"),
        env.build_call_graph(),
        env.load_call_graph(),
    ):
        pass

    # We get the view of the call graph for the chunk with books.py and
    # titles.py.
    #
    # There should be a function view for every function and method in the
    # chunk.
    if env.step(
        env.get_call_graph_view(["myapp/books.py", "myapp/titles.py"]),
    ):
        assert {view.location for view in env.view.function_views} == {
            "myapp/books.py:Book.__init__",
            "myapp/books.py:Book.save",
            "myapp/books.py:Book._validate",
            "myapp/books.py:create_book",
            "myapp/titles.py:format_title",
            "myapp/titles.py:capitalize",
        }

    # We look at the view of create_book.
    #
    # Its callees should be labelled as in the same module, or in another
    # module of the chunk.
    if env.step():
        create_book_view = env.function_view("myapp/books.py:create_book")
        assert env.calls(create_book_view.callees) == {
            ("myapp/books.py:Book.__init__", CallScopes.SAME_MODULE, True, None),
            ("myapp/titles.py:format_title", CallScopes.CHUNK, True, None),
        }
        assert create_book_view.callers == []

    # We look at the view of capitalize.
    #
    # A caller outside the chunk should be labelled as such, with the first
    # responsibility from its node file.
    if env.step():
        assert env.calls(env.function_view("myapp/titles.py:capitalize").callers) == {
            ("myapp/titles.py:format_title", CallScopes.SAME_MODULE, True, None),
            (
                "myapp/authors.py:Author.__init__",
                CallScopes.OUTSIDE_CHUNK,
                True,
                "Creates an author",
            ),
        }

    # We look at the view of Book.save.
    #
    # The uncertain caller should be marked as uncertain.
    if env.step():
        assert env.calls(env.function_view("myapp/books.py:Book.save").callers) == {
            (
                "myapp/authors.py:publish",
                CallScopes.OUTSIDE_CHUNK,
                False,
                "Publishes a book or an author",
            ),
        }


class Env(TestEnv):
    def __post_init__(self):
        self.view: CallGraphView = None

    def create_module_node_file(self, module_name: str) -> None:
        create_module_node_file(self.source_root, module_name)

    def add_responsibility(
        self, module_name: str, location: str, responsibility: str
    ) -> None:
        add_responsibility(self.source_root, module_name, location, responsibility)

    def get_call_graph_view(
        self, chunk_module_names: T.List[str], max_callers: int = 10
    ) -> None:
        self.view = get_call_graph_view(
            self.call_graph, self.source_root, chunk_module_names, max_callers
        )

    # Queries (for use in asserts)

    def function_view(self, location: str) -> FunctionView:
        matches = [v for v in self.view.function_views if v.location == location]
        assert len(matches) == 1, f"Expected one function view for {location}"
        return matches[0]

    def calls(self, call_views) -> T.Set[T.Tuple]:
        return {
            (call.location, call.scope, call.is_certain, call.responsibility)
            for call in call_views
        }
