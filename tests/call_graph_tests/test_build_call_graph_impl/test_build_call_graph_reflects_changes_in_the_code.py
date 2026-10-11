from call_graph_tests.call_graph_test_env import Context, TestEnv

# titles.py after capitalize has moved to text.py. It imports capitalize, so
# that `titles.capitalize` (as used by authors.py) still works.
TITLES_PY = """\
from myapp.text import capitalize


def format_title(title):
    return capitalize(title.strip())
"""

TEXT_PY = """\
def capitalize(text):
    return text.title()
"""


def create_env(context: Context):
    return Env(context)


def test_build_call_graph_reflects_changes_in_the_code(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the modules myapp/titles.py, myapp/books.py and myapp/authors.py,
    # and their call graph.
    if env.step(
        env.write_myapp_modules(),
        env.build_call_graph(),
    ):
        pass

    # We move capitalize from titles.py to the new module text.py, and build
    # the call graph again.
    #
    # The calls of capitalize should be edges to its new location, also the
    # call in authors.py, which did not change.
    if env.step(
        env.write_module("myapp/titles.py", TITLES_PY),
        env.write_module("myapp/text.py", TEXT_PY),
        env.build_call_graph(),
        env.load_call_graph(),
    ):
        assert env.callees_of("myapp/titles.py:format_title") == {
            ("myapp/text.py:capitalize", True)
        }
        assert env.callees_of("myapp/authors.py:Author.__init__") == {
            ("myapp/text.py:capitalize", True)
        }

    # We delete authors.py, and build the call graph again.
    #
    # There should be no edges from authors.py, and no uncertain edge to its
    # Author.save method.
    if env.step(
        env.delete_module("myapp/authors.py"),
        env.build_call_graph(),
        env.load_call_graph(),
    ):
        assert all(edge.file != "myapp/authors.py" for edge in env.call_graph.edges)
        assert all(
            edge.callee != "myapp/authors.py:Author.save"
            for edge in env.call_graph.edges
        )


class Env(TestEnv):
    pass
