from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.remove_responsibility import remove_responsibility
from groupy.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)
from groupy.functions.actions.update_step import update_step
from groupy.nodes.utils.exceptions import (
    FieldNotSupportedError,
    InvalidIndexError,
    InvalidValueError,
)
from node_edits_tests.node_edits_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_edit_function_analysis_rejects_invalid_edits(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file, in which
    # create_book has two steps and no responsibilities.
    if env.step(
        env.create_module_with_node_file(),
        env.edit_node_file(add_step, "create_book", "Format the title"),
        env.edit_node_file(add_step, "create_book", "Create the book"),
        env.remember_node_file(),
    ):
        pass

    # We update the third step, insert a step after the end of the list, and
    # remove a responsibility at a negative index.
    #
    # Each should raise an InvalidIndexError and leave the node file
    # unchanged.
    if env.step(
        env.edit_node_file_and_catch_error(update_step, "create_book", 2, "Log"),
    ):
        assert isinstance(env.error, InvalidIndexError)

    if env.step(
        env.edit_node_file_and_catch_error(add_step, "create_book", "Log", 3),
    ):
        assert isinstance(env.error, InvalidIndexError)

    if env.step(
        env.edit_node_file_and_catch_error(remove_responsibility, "create_book", -1),
    ):
        assert isinstance(env.error, InvalidIndexError)
        assert env.node_file_is_unchanged()

    # We set an extract-method priority that does not exist.
    #
    # It should raise an InvalidValueError.
    if env.step(
        env.edit_node_file_and_catch_error(
            set_extract_method_priority, "create_book", "urgent"
        ),
    ):
        assert isinstance(env.error, InvalidValueError)

    # We add a step to the Book class, and set the extract-method priority of
    # the MAX_CHAPTERS variable.
    #
    # A class node has no steps and a variable node has no priority, so each
    # should raise a FieldNotSupportedError.
    if env.step(
        env.edit_node_file_and_catch_error(add_step, "Book", "Store the title"),
    ):
        assert isinstance(env.error, FieldNotSupportedError)

    if env.step(
        env.edit_node_file_and_catch_error(
            set_extract_method_priority, "MAX_CHAPTERS", "low"
        ),
    ):
        assert isinstance(env.error, FieldNotSupportedError)
        assert env.node_file_is_unchanged()


class Env(TestEnv):
    pass
