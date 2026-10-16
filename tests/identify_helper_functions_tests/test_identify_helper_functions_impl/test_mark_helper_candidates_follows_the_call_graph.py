from identify_helper_functions_tests.identify_helper_functions_test_env import (
    Context,
    TestEnv,
)

TITLES_PY = """\
class Title:
    def __init__(self, text):
        self.text = _clean(text)

    def save(self):
        self._validate()
        log("saved")

    def _validate(self):
        assert self.text


def create_title(text):
    log("created")
    return Title(format_title(text))


def format_title(text):
    return capitalize(text)


def capitalize(text):
    return text.title()


def _clean(text):
    return text.strip()


def log(message):
    print(message)


def publish(item):
    item.save()


def get_default_text():
    return "Untitled"


DEFAULT_TEXT = get_default_text()
"""

AUTHORS_PY = """\
from myapp.titles import capitalize


def create_author_name(name):
    return _trim(capitalize(name))


def _trim(name):
    return name.strip()
"""


def create_env(context: Context):
    return Env(context)


def test_mark_helper_candidates_follows_the_call_graph(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, with the modules titles.py and
    # authors.py, and the call graph of the target code.
    if env.step(
        env.create_session_with_modules(
            {"myapp/titles.py": TITLES_PY, "myapp/authors.py": AUTHORS_PY}
        ),
        env.build_call_graph(),
    ):
        pass

    # We mark the helper candidates of titles.py.
    #
    # A function or method should be a helper candidate when it has exactly
    # one caller, which is a function or method in the same module, through a
    # certain edge.
    if env.step(
        env.mark_helper_candidates(["myapp/titles.py"]),
        env.load_module_node("myapp/titles.py"),
    ):
        assert env.helper_candidates() == {
            "Title._validate",
            "format_title",
            "_clean",
        }
        # Not helper candidates:
        # - Title.__init__ (called by create_title) is a dunder method;
        # - Title.save is called through an uncertain edge (by publish);
        # - create_title and publish have no callers;
        # - capitalize is also called from another module;
        # - log is called by two functions;
        # - get_default_text is called from module-level code.

    # We look at the node file of authors.py.
    #
    # Only the modules that are passed should be marked, so _trim should not
    # be marked, although it is called by one function in its module.
    if env.step(
        env.load_module_node("myapp/authors.py"),
    ):
        assert env.helper_candidates() == set()


class Env(TestEnv):
    pass
