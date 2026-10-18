from stage_tests.e2e_test_env import Context, TestEnv

from groupy.functions.actions.add_step import add_step

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


def create_env(context: Context):
    return Env(context)


def test_propose_move_steps_to_caller_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is
    # propose-move-steps-to-caller. The function format_invoice, whose only
    # caller is print_invoice, marks the invoice as printed, which is clearly
    # a step of print_invoice.
    if env.step(
        env.create_session_with_claude({INVOICES: INVOICES_PY}),
        env.edit_node_file(add_step, INVOICES, "print_invoice", "Format the invoice"),
        env.edit_node_file(add_step, INVOICES, "print_invoice", "Print the text"),
        env.edit_node_file(add_step, INVOICES, "format_invoice", MARK_STEP),
        env.edit_node_file(
            add_step, INVOICES, "format_invoice", "Format the id and the amount"
        ),
        env.set_next_stage("propose-move-steps-to-caller"),
    ):
        pass

    # We run groupy next.
    #
    # The stage should have finished with a clean working tree, without
    # changes to the source.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "apply-move-steps-to-caller"
        assert env.git_status() == ""
        assert env.read_module(INVOICES) == INVOICES_PY

    # We look at the node file of invoices.py.
    #
    # Claude should have proposed to move the marking step to the caller, and
    # nothing else.
    if env.step(
        env.load_module_node(INVOICES),
    ):
        assert env.function_node("format_invoice").steps_to_move_to_caller == [
            MARK_STEP
        ]
        assert env.function_node("print_invoice").steps_to_move_to_caller == []


class Env(TestEnv):
    pass
