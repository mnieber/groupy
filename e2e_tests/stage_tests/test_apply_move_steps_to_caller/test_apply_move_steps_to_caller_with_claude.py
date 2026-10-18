from stage_tests.e2e_test_env import Context, TestEnv

from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)

INVOICES = "myapp/invoices.py"

INVOICES_PY = """\
def print_invoice(invoice):
    text = format_invoice(invoice)
    print(text)


def format_invoice(invoice):
    invoice["is_printed"] = True
    return f"Invoice {invoice['id']}: {invoice['amount']:.2f}"
"""

MARK_STEP = "Mark the invoice as printed"

# Prints the invoice, and returns the invoice, to show that it is marked
EXAMPLE = (
    '(lambda invoice: (print_invoice(invoice), invoice)[1])({"id": 7, "amount": 2.5})'
)


def create_env(context: Context):
    return Env(context)


def test_apply_move_steps_to_caller_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is
    # apply-move-steps-to-caller. The step of format_invoice that marks the
    # invoice as printed should move to its only caller, print_invoice.
    if env.step(
        env.create_session_with_claude({INVOICES: INVOICES_PY}),
        env.edit_node_file(add_step, INVOICES, "print_invoice", "Format the invoice"),
        env.edit_node_file(add_step, INVOICES, "print_invoice", "Print the text"),
        env.edit_node_file(add_step, INVOICES, "format_invoice", MARK_STEP),
        env.edit_node_file(
            add_step, INVOICES, "format_invoice", "Format the id and the amount"
        ),
        env.edit_node_file(
            add_step_to_move_to_caller, INVOICES, "format_invoice", MARK_STEP
        ),
        env.set_next_stage("apply-move-steps-to-caller"),
        env.remember_behaviour(INVOICES, EXAMPLE),
    ):
        assert "'is_printed': True" in env.remembered_behaviour

    # We run groupy next.
    #
    # Claude should have moved the step in an RFR and committed it with
    # commit_refactoring, so that the stage finished with a clean working
    # tree.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "propose-module-layout"
        assert env.git_status() == ""

    # We look at invoices.py.
    #
    # The marking should have moved from format_invoice to print_invoice,
    # and the code should behave the same.
    if env.step():
        assert "is_printed" not in env.function_source(INVOICES, "format_invoice")
        assert "is_printed" in env.function_source(INVOICES, "print_invoice")
        assert env.behaviour(INVOICES, EXAMPLE) == env.remembered_behaviour

    # We look at the node file of invoices.py.
    #
    # The step should have moved from format_invoice to print_invoice.
    if env.step(
        env.load_module_node(INVOICES),
    ):
        assert MARK_STEP not in env.function_node("format_invoice").steps
        assert env.function_node("format_invoice").steps_to_move_to_caller == []
        assert len(env.function_node("print_invoice").steps) == 3


class Env(TestEnv):
    pass
