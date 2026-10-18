from stage_tests.e2e_test_env import Context, TestEnv

BOOKS_PY = """\
def create_book(title):
    return {"title": _normalize_title(title), "slug": make_slug(title)}


def _normalize_title(title):
    return " ".join(title.split()).title()


def make_slug(text):
    return "-".join(text.lower().split())
"""

CHAPTERS_PY = """\
from myapp.books import make_slug


def create_chapter(book, title):
    return {"book": book["slug"], "slug": make_slug(title)}
"""


def create_env(context: Context):
    return Env(context)


def test_identify_helper_functions_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, for the modules books.py and
    # chapters.py. In books.py, create_book is the only caller of
    # _normalize_title and of make_slug, but make_slug is also called from
    # chapters.py.
    if env.step(
        env.create_session_with_claude(
            {"myapp/books.py": BOOKS_PY, "myapp/chapters.py": CHAPTERS_PY}
        ),
    ):
        pass

    # We run groupy next.
    #
    # Claude should have answered the RFA with callbacks that Groupy could
    # run, so that the stage finished and the working tree is clean.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "analyze-terminology"
        assert env.git_status() == ""

    # We look at the node file of books.py.
    #
    # Claude should have nested _normalize_title under create_book, but not
    # make_slug, because it is called from outside the module.
    if env.step(
        env.load_module_node("myapp/books.py"),
    ):
        assert env.names(env.module_node.function_nodes) == [
            "create_book",
            "make_slug",
        ]
        assert env.helper_names("create_book") == ["_normalize_title"]
        assert env.helper_names("make_slug") == []


class Env(TestEnv):
    pass
