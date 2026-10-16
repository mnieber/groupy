from identify_helper_functions_tests.identify_helper_functions_test_env import (
    Context,
    TestEnv,
)

TITLES_PY = """\
class Title:
    def __init__(self, text):
        self.text = clean(text)


def format_title(text):
    return capitalize(_trim(text))


def capitalize(text):
    return text.title()


def clean(text):
    return text.strip()


def _trim(text):
    return text.strip()
"""

AUTHORS_PY = """\
from myapp.titles import capitalize


def create_author_name(name):
    return capitalize(name)
"""

RENAMED_TITLES_PY = """\
class Title:
    def __init__(self, text):
        self.text = _clean(text)


def format_title(text):
    return _capitalize(_trim(text))


def _capitalize(text):
    return text.title()


def _clean(text):
    return text.strip()


def _trim(text):
    return text.strip()
"""

RENAMED_AUTHORS_PY = """\
from myapp.titles import _capitalize


def create_author_name(name):
    return _capitalize(name)
"""


def create_env(context: Context):
    return Env(context)


def test_rename_helper_functions_renames_helpers_and_call_sites(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, with the modules titles.py and
    # authors.py. In the node file of titles.py, clean is a helper function
    # of the Title.__init__ method, and capitalize and _trim are helper
    # functions of format_title. Although authors.py also calls capitalize,
    # Claude has nested it.
    if env.step(
        env.create_session_with_modules(
            {"myapp/titles.py": TITLES_PY, "myapp/authors.py": AUTHORS_PY}
        ),
        env.move_function_to_parent("myapp/titles.py", "clean", "Title.__init__"),
        env.move_function_to_parent("myapp/titles.py", "capitalize", "format_title"),
        env.move_function_to_parent("myapp/titles.py", "_trim", "format_title"),
    ):
        pass

    # We rename the helper functions of titles.py.
    #
    # The helper function nodes should be renamed to start with an
    # underscore, also the helper of the method. _trim should keep its name.
    if env.step(
        env.rename_helper_functions(["myapp/titles.py"]),
        env.load_module_node("myapp/titles.py"),
    ):
        assert env.helper_names("Title.__init__") == ["_clean"]
        assert env.helper_names("format_title") == ["_capitalize", "_trim"]
        assert env.names(env.module_node.function_nodes) == ["format_title"]

    # We look at the modules.
    #
    # The functions should be renamed in the source, including all call sites
    # (also the import and the call in authors.py).
    if env.step():
        assert env.read_module("myapp/titles.py") == RENAMED_TITLES_PY
        assert env.read_module("myapp/authors.py") == RENAMED_AUTHORS_PY


class Env(TestEnv):
    pass
