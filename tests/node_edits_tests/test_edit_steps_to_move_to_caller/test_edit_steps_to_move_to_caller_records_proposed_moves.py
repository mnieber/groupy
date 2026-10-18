from node_edits_tests.node_edits_test_env import Context, TestEnv

from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from groupy.functions.actions.remove_step import remove_step
from groupy.functions.actions.remove_step_to_move_to_caller import (
    remove_step_to_move_to_caller,
)
from groupy.functions.actions.update_step import update_step


def create_env(context: Context):
    return Env(context)


def test_edit_steps_to_move_records_proposed_moves(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file, in which
    # create_book has three steps.
    if env.step(
        env.create_module_with_node_file(),
        env.edit_node_file(add_step, "create_book", "Format the title"),
        env.edit_node_file(add_step, "create_book", "Validate the title"),
        env.edit_node_file(add_step, "create_book", "Create the book"),
    ):
        pass

    # We propose to move the second and the first step to the caller.
    #
    # The steps to move should be listed in the order of the steps.
    if env.step(
        env.edit_node_file(
            add_step_to_move_to_caller, "create_book", "Validate the title"
        ),
        env.edit_node_file(
            add_step_to_move_to_caller, "create_book", "Format the title"
        ),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").steps_to_move_to_caller == [
            "Format the title",
            "Validate the title",
        ]

    # We update the second step, and remove the first step.
    #
    # The steps to move should follow the steps: the updated step should be
    # updated, and the removed step should be removed (which is how a moved
    # step stops being proposed).
    if env.step(
        env.edit_node_file(
            update_step, "create_book", 1, "Validate the title of the book"
        ),
        env.edit_node_file(remove_step, "create_book", 0),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").steps_to_move_to_caller == [
            "Validate the title of the book"
        ]

    # We withdraw the proposal to move the remaining step.
    #
    # There should be no steps to move, and the step should stay.
    if env.step(
        env.edit_node_file(
            remove_step_to_move_to_caller,
            "create_book",
            "Validate the title of the book",
        ),
        env.load_module_node(),
    ):
        create_book_node = env.function_node("create_book")
        assert create_book_node.steps_to_move_to_caller == []
        assert create_book_node.steps == [
            "Validate the title of the book",
            "Create the book",
        ]
        # The edits only change the node file.
        assert env.module_is_unchanged()


class Env(TestEnv):
    pass
