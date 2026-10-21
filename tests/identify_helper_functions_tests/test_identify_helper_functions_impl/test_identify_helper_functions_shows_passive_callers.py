from identify_helper_functions_tests.identify_helper_functions_test_env import (
    RFA_ID,
    Context,
    TestEnv,
)

from groupy.call_graph.enums import CallScopes

SUMMARY = "myapp/reports/summary.py"

SUMMARY_PY = """\
from myapp.books import create_book


def summarize(title):
    return format_summary(create_book(title).title)


def format_summary(text):
    return text.upper()
"""


def create_env(context: Context):
    return Env(context)


def test_identify_helper_functions_shows_passive_callers(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, where all modules are in one
    # chunk. Besides the modules of the base env, myapp has the reports
    # package, which the developer excludes. The summarize function in the
    # reports package calls create_book, and is the only caller of
    # format_summary.
    if env.step(
        env.create_session_with_modules(
            {"myapp/reports/__init__.py": "", SUMMARY: SUMMARY_PY}
        ),
        env.set_session_exclude("myapp/reports/**"),
        env.script_rfa(RFA_ID),
    ):
        pass

    # We run groupy next.
    #
    # The call graph view in the RFA should only have the functions of the
    # active modules, but their callers should include the passive caller,
    # which is outside the (filtered) chunk.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.function_locations_in_context(RFA_ID) == {
            "myapp/books.py:Book.__init__",
            "myapp/books.py:create_book",
            "myapp/books.py:_normalize_title",
            "myapp/chapters/create_chapter.py:create_chapter",
        }
        assert env.callers_in_context(RFA_ID, "myapp/books.py:create_book") == {
            (f"{SUMMARY}:summarize", CallScopes.OUTSIDE_CHUNK, True),
        }

    # We look at the node file of the summary module.
    #
    # The stage should not have marked the helper candidates of the passive
    # module.
    if env.step(
        env.load_module_node(SUMMARY),
    ):
        assert env.function_node("format_summary").is_helper_candidate is False


class Env(TestEnv):
    def function_locations_in_context(self, rfa_id: str):
        view = self.rfa(rfa_id).context["call_graph_view"]
        return {function_view.location for function_view in view.function_views}
