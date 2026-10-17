from breaker.functions.actions.add_step import add_step
from breaker.functions.actions.add_step_to_move_to_caller import (
    add_step_to_move_to_caller,
)
from breaker.functions.actions.remove_step_to_move import remove_step_to_move
from breaker.nodes.utils.exceptions import EntryNotFoundError, InvalidValueError
from node_edits_tests.node_edits_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_edit_steps_to_move_rejects_invalid_edits(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file, in which
    # create_book has one step, which is proposed to move to the caller.
    if env.step(
        env.create_module_with_node_file(),
        env.edit_node_file(add_step, "create_book", "Format the title"),
        env.edit_node_file(
            add_step_to_move_to_caller, "create_book", "Format the title"
        ),
        env.remember_node_file(),
    ):
        pass

    # We propose to move a step that create_book does not have.
    #
    # It should raise an InvalidValueError and leave the node file unchanged.
    if env.step(
        env.edit_node_file_and_catch_error(
            add_step_to_move_to_caller, "create_book", "Log the title"
        ),
    ):
        assert isinstance(env.error, InvalidValueError)
        assert env.node_file_is_unchanged()

    # We withdraw a proposal that create_book does not have.
    #
    # It should raise an EntryNotFoundError and leave the node file
    # unchanged.
    if env.step(
        env.edit_node_file_and_catch_error(
            remove_step_to_move, "create_book", "Log the title"
        ),
    ):
        assert isinstance(env.error, EntryNotFoundError)
        assert env.node_file_is_unchanged()

    # We propose to move the same step again.
    #
    # The step should be listed once.
    if env.step(
        env.edit_node_file(
            add_step_to_move_to_caller, "create_book", "Format the title"
        ),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").steps_to_move_to_caller == [
            "Format the title"
        ]


class Env(TestEnv):
    pass
