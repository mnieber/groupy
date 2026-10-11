from call_graph_tests.call_graph_test_env import Context, TestEnv

FILES_PY = """\
import os


def get_path(name):
    print(name)
    return os.path.join("books", clean(name))


def clean(name):
    return name.strip()
"""

TEST_FILES_PY = """\
from myapp.files import get_path


def test_get_path():
    assert get_path("a") == "books/a"
"""

CONFTEST_PY = """\
from myapp.files import clean


def make_name():
    return clean(" a ")
"""


def create_env(context: Context):
    return Env(context)


def test_build_call_graph_ignores_test_code_and_external_calls(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/files.py, which calls functions of the standard
    # library, and test code that calls myapp/files.py: a tests dir, a
    # test_*.py module next to the code, and a conftest.py.
    if env.step(
        env.write_module("myapp/__init__.py", ""),
        env.write_module("myapp/files.py", FILES_PY),
        env.write_module("myapp/test_files.py", TEST_FILES_PY),
        env.write_module("myapp/conftest.py", CONFTEST_PY),
        env.write_module("tests/test_paths.py", TEST_FILES_PY),
    ):
        pass

    # We build the call graph.
    #
    # Calls of functions outside the target code should not be edges.
    if env.step(
        env.build_call_graph(),
        env.load_call_graph(),
    ):
        assert env.callees_of("myapp/files.py:get_path") == {
            ("myapp/files.py:clean", True)
        }

    # We look at the callers in the call graph.
    #
    # Test code should be ignored, so all edges should start in
    # myapp/files.py.
    if env.step():
        assert {edge.file for edge in env.call_graph.edges} == {"myapp/files.py"}


class Env(TestEnv):
    pass
