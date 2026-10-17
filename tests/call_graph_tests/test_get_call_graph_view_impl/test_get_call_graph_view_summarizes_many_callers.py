import typing as T

from groupy.call_graph.models.call_graph_view import CallGraphView, FunctionView
from groupy.call_graph.rules.get_call_graph_view import get_call_graph_view
from call_graph_tests.call_graph_test_env import Context, TestEnv

LOGS_PY = """\
def log(message):
    print(message)
"""

BOOKS_PY = """\
from myapp.logs import log


def create_book(title):
    log("Creating")
    log(title)


def delete_book(title):
    log(title)


def rename_book(title):
    log(title)
"""

AUTHORS_PY = """\
from myapp.logs import log


def create_author(name):
    log(name)
"""


def create_env(context: Context):
    return Env(context)


def test_get_call_graph_view_summarizes_many_callers(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the function log, which is called by four functions in two
    # modules. create_book calls it twice.
    if env.step(
        env.write_module("myapp/__init__.py", ""),
        env.write_module("myapp/logs.py", LOGS_PY),
        env.write_module("myapp/books.py", BOOKS_PY),
        env.write_module("myapp/authors.py", AUTHORS_PY),
        env.build_call_graph(),
        env.load_call_graph(),
    ):
        pass

    # We get the view for the chunk with logs.py, with at most four callers
    # per function.
    #
    # The four callers of log should be listed, each caller once (also
    # create_book, which calls log twice).
    if env.step(
        env.get_call_graph_view(["myapp/logs.py"], max_callers=4),
    ):
        log_view = env.function_view("myapp/logs.py:log")
        assert sorted(call.location for call in log_view.callers) == [
            "myapp/authors.py:create_author",
            "myapp/books.py:create_book",
            "myapp/books.py:delete_book",
            "myapp/books.py:rename_book",
        ]
        assert log_view.caller_summary is None

    # We get the view again, with at most three callers per function.
    #
    # Instead of the callers, the view of log should have a summary that
    # counts the places of the calls and the modules.
    if env.step(
        env.get_call_graph_view(["myapp/logs.py"], max_callers=3),
    ):
        log_view = env.function_view("myapp/logs.py:log")
        assert log_view.callers == []
        assert log_view.caller_summary == "called from 5 places in 2 modules"


class Env(TestEnv):
    def __post_init__(self):
        self.view: CallGraphView = None

    def get_call_graph_view(
        self, chunk_module_names: T.List[str], max_callers: int
    ) -> None:
        self.view = get_call_graph_view(
            self.call_graph, self.source_root, chunk_module_names, max_callers
        )

    # Queries (for use in asserts)

    def function_view(self, location: str) -> FunctionView:
        matches = [v for v in self.view.function_views if v.location == location]
        assert len(matches) == 1, f"Expected one function view for {location}"
        return matches[0]
