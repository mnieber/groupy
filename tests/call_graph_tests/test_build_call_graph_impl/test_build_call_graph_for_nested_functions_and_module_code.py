from call_graph_tests.call_graph_test_env import Context, TestEnv

REPORTS_PY = """\
def create_report(rows):
    def _format_row(row):
        return format_cell(row[0])

    return [_format_row(row) for row in rows]


def format_cell(cell):
    return str(cell)


EMPTY_REPORT = create_report([])
"""


def create_env(context: Context):
    return Env(context)


def test_build_call_graph_for_nested_functions_and_module_code(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a module in which create_report has a nested function that
    # calls format_cell, and in which module-level code calls create_report.
    if env.step(
        env.write_module("myapp/__init__.py", ""),
        env.write_module("myapp/reports.py", REPORTS_PY),
        env.build_call_graph(),
        env.load_call_graph(),
    ):
        pass

    # We look at the calls of create_report.
    #
    # A nested function is part of the body of its enclosing function, so the
    # call of format_cell should be an edge of create_report, and the call of
    # the nested function should not be an edge.
    if env.step():
        assert env.callees_of("myapp/reports.py:create_report") == {
            ("myapp/reports.py:format_cell", True)
        }
        assert env.edge(
            "myapp/reports.py:create_report", "myapp/reports.py:format_cell"
        ).line == env.line_of("myapp/reports.py", "return format_cell(row[0])")

    # We look at the module-level code.
    #
    # Its call should be an edge from <file>:@module.
    if env.step():
        assert env.callees_of("myapp/reports.py:@module") == {
            ("myapp/reports.py:create_report", True)
        }


class Env(TestEnv):
    pass
