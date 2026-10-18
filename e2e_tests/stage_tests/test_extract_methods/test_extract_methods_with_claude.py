from stage_tests.e2e_test_env import Context, TestEnv

from groupy.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)

REPORTS = "myapp/reports.py"

REPORTS_PY = """\
def create_report(orders):
    if not orders:
        raise ValueError("There are no orders")
    for order in orders:
        if order["qty"] <= 0:
            raise ValueError(f"Invalid quantity in order {order['id']}")

    lines = []
    for order in orders:
        lines.append(f"{order['id']}: {order['qty']} x {order['price']:.2f}")
    total = sum(order["qty"] * order["price"] for order in orders)
    lines.append(f"Total: {total:.2f}")
    return "\\n".join(lines)
"""

EXAMPLE = (
    'create_report([{"id": 1, "qty": 2, "price": 3.5}, '
    '{"id": 2, "qty": 1, "price": 10}])'
)


def create_env(context: Context):
    return Env(context)


def test_extract_methods_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is extract-methods.
    # The function create_report validates the orders, and then formats a
    # report. It has the extract_method_priority high.
    if env.step(
        env.create_session_with_claude({REPORTS: REPORTS_PY}),
        env.edit_node_file(
            set_extract_method_priority, REPORTS, "create_report", "high"
        ),
        env.set_next_stage("extract-methods"),
        env.remember_behaviour(REPORTS, EXAMPLE),
    ):
        assert "Total: 17.00" in env.remembered_behaviour

    # We run groupy next.
    #
    # Claude should have extracted at least one function, each in an RFR made
    # by the extract_method callback, and finished the candidate, so that the
    # stage finished with a clean working tree.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "propose-move-steps-to-caller"
        assert env.git_status() == ""

    # We look at reports.py.
    #
    # create_report should call a new function, and still behave the same.
    if env.step():
        new_names = set(env.top_level_function_names(REPORTS)) - {"create_report"}
        assert new_names
        assert env.called_names(REPORTS, "create_report") & new_names
        assert env.behaviour(REPORTS, EXAMPLE) == env.remembered_behaviour


class Env(TestEnv):
    pass
