from node_edits_tests.node_edits_test_env import Context, TestEnv

from groupy.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)
from groupy.nodes.utils.exceptions import (
    EmbeddedFunctionNodeNotFoundError,
    NodeNotFoundError,
)

REPORT_PY = """\
def create_report(rows):
    def _format_line(row):
        def _pad(text):
            return text.ljust(10)

        return _pad(str(row))

    if rows:
        def _format_header():
            return "Report"

    return [_format_line(row) for row in rows]


class Report:
    def render(self, rows):
        def _format_row(row):
            return str(row)

        return [_format_row(row) for row in rows]
"""


def create_env(context: Context):
    return Env(context)


def test_edit_explains_embedded_functions(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a module with functions that are embedded in a function (also two
    # levels deep, in an if block, and in a method).
    if env.step(
        env.create_module_with_node_file("myapp/report.py", REPORT_PY),
        env.remember_node_file(),
    ):
        pass

    # We edit the nodes of embedded functions, by full location and by the
    # last part of it.
    #
    # Each should raise an EmbeddedFunctionNodeNotFoundError that names the
    # function and its parent, and tells not to retry. The node file should
    # stay unchanged.
    for location, parent in (
        ("create_report._format_line", "create_report"),
        ("_format_line", "create_report"),
        ("create_report._format_line._pad", "create_report._format_line"),
        ("create_report._format_header", "create_report"),
        ("Report.render._format_row", "Report.render"),
    ):
        if env.step(
            env.edit_node_file_and_catch_error(
                set_extract_method_priority, location, "low"
            ),
        ):
            assert isinstance(env.error, EmbeddedFunctionNodeNotFoundError)
            assert isinstance(env.error, NodeNotFoundError)
            message = str(env.error)
            assert "embedded in " + parent in message
            assert "don't retry" in message
            assert env.node_file_is_unchanged()

    # We edit a location that is not an embedded function.
    #
    # It should still raise a plain NodeNotFoundError.
    if env.step(
        env.edit_node_file_and_catch_error(
            set_extract_method_priority, "create_report._format_lines", "low"
        ),
    ):
        assert type(env.error) is NodeNotFoundError

    # We edit a function that has a node.
    #
    # It should work.
    if env.step(
        env.edit_node_file_and_catch_error(
            set_extract_method_priority, "create_report", "low"
        ),
    ):
        assert env.error is None


class Env(TestEnv):
    pass
