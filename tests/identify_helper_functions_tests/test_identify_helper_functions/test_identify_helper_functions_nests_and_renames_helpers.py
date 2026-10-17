from groupy.call_graph.enums import CallScopes
from groupy_next_tests.groupy_next_test_env import callback
from identify_helper_functions_tests.identify_helper_functions_test_env import (
    RFA_ID,
    Context,
    TestEnv,
)

REPORTS_PY = """\
def create_report(user):
    lines = format_lines(user.stats)
    return join_lines(lines)


def format_lines(stats):
    return [format_stat(stat) for stat in stats]


def format_stat(stat):
    return f"{stat.name}: {stat.value}"


def join_lines(lines):
    return "\\n".join(lines)


def send_report(user):
    text = create_report(user)
    return join_lines([text, "--"])
"""

RENAMED_REPORTS_PY = """\
def create_report(user):
    lines = _format_lines(user.stats)
    return join_lines(lines)


def _format_lines(stats):
    return [_format_stat(stat) for stat in stats]


def _format_stat(stat):
    return f"{stat.name}: {stat.value}"


def join_lines(lines):
    return "\\n".join(lines)


def send_report(user):
    text = create_report(user)
    return join_lines([text, "--"])
"""


def create_env(context: Context):
    return Env(context)


def test_identify_helper_functions_nests_and_renames_helpers(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, where all modules are in one
    # chunk. Besides books.py (where create_book calls _normalize_title and
    # Book), myapp has reports.py. The RFA of the chunk nests format_stat
    # under format_lines, format_lines under create_report, and
    # _normalize_title under create_book. It doesn't nest create_report,
    # although it is a helper candidate.
    if env.step(
        env.create_session_with_modules({"myapp/reports.py": REPORTS_PY}),
        env.script_rfa(
            RFA_ID,
            callback(
                "move_function_to_parent",
                module_name="myapp/reports.py",
                function_location="format_stat",
                parent_location="format_lines",
            ),
            callback(
                "move_function_to_parent",
                module_name="myapp/reports.py",
                function_location="format_lines",
                parent_location="create_report",
            ),
            callback(
                "move_function_to_parent",
                module_name="myapp/books.py",
                function_location="_normalize_title",
                parent_location="create_book",
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should have marked the helper candidates, run the callbacks,
    # renamed the helper functions and finished the chunk and the stage,
    # committing after each step.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.commit_messages_since_remembered_head() == [
            "identify-helper-functions: mark_helper_candidates",
            "identify-helper-functions: move_function_to_parent",
            "identify-helper-functions: move_function_to_parent",
            "identify-helper-functions: move_function_to_parent",
            "identify-helper-functions: rename_helper_functions",
            "identify-helper-functions: finish group-1/chunk-1",
            "identify-helper-functions: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the RFA.
    #
    # Its context should contain the call graph view of the chunk, with the
    # callers of each function.
    if env.step():
        assert env.callers_in_context(RFA_ID, "myapp/reports.py:format_stat") == {
            ("myapp/reports.py:format_lines", CallScopes.SAME_MODULE, True),
        }
        assert env.callers_in_context(RFA_ID, "myapp/reports.py:join_lines") == {
            ("myapp/reports.py:create_report", CallScopes.SAME_MODULE, True),
            ("myapp/reports.py:send_report", CallScopes.SAME_MODULE, True),
        }

    # We look at the node file of reports.py.
    #
    # The helper functions should be nested, and renamed to start with an
    # underscore. The helper candidates should still be marked, including
    # create_report, which Claude did not nest.
    if env.step(
        env.load_module_node("myapp/reports.py"),
    ):
        assert env.names(env.module_node.function_nodes) == [
            "create_report",
            "join_lines",
            "send_report",
        ]
        assert env.helper_names("create_report") == ["_format_lines"]
        assert env.helper_names("create_report._format_lines") == ["_format_stat"]
        assert env.helper_candidates() == {
            "create_report",
            "create_report._format_lines",
            "create_report._format_lines._format_stat",
        }

    # We look at reports.py.
    #
    # The helper functions should be renamed, including their call sites. In
    # the source, they should stay top-level functions.
    if env.step():
        assert env.read_module("myapp/reports.py") == RENAMED_REPORTS_PY

    # We look at the node file of books.py.
    #
    # _normalize_title should be nested under create_book. Since its name
    # already starts with an underscore, it should not be renamed.
    if env.step(
        env.load_module_node("myapp/books.py"),
    ):
        assert env.helper_names("create_book") == ["_normalize_title"]
        assert env.helper_candidates() == {"create_book._normalize_title"}
        assert "def _normalize_title(title):" in env.read_module("myapp/books.py")

    # We look at the session.
    #
    # The next stage should be analyze-terminology.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "analyze-terminology"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
