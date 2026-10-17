from groupy.nodes.actions.set_code_unit_type import set_code_unit_type
from groupy.nodes.actions.set_move_to_file import set_move_to_file
from groupy.nodes.utils.exceptions import FieldNotSupportedError, InvalidValueError
from node_edits_tests.node_edits_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_set_node_fields_rejects_invalid_values(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file.
    if env.step(
        env.create_module_with_node_file(),
        env.remember_node_file(),
    ):
        pass

    # We set a code unit type that belongs to another kind of node: "model"
    # for a function, "action" for a class and "rule" for a variable.
    #
    # Each should raise an InvalidValueError and leave the node file
    # unchanged.
    if env.step(
        env.edit_node_file_and_catch_error(set_code_unit_type, "create_book", "model"),
    ):
        assert isinstance(env.error, InvalidValueError)
        assert env.node_file_is_unchanged()

    if env.step(
        env.edit_node_file_and_catch_error(set_code_unit_type, "Book", "action"),
    ):
        assert isinstance(env.error, InvalidValueError)

    if env.step(
        env.edit_node_file_and_catch_error(set_code_unit_type, "MAX_CHAPTERS", "rule"),
    ):
        assert isinstance(env.error, InvalidValueError)
        assert env.node_file_is_unchanged()

    # We set the code unit type and the target file of the module node.
    #
    # A module node has neither field, so each should raise a
    # FieldNotSupportedError.
    if env.step(
        env.edit_node_file_and_catch_error(set_code_unit_type, "@module", "action"),
    ):
        assert isinstance(env.error, FieldNotSupportedError)

    if env.step(
        env.edit_node_file_and_catch_error(
            set_move_to_file, "@module", "myapp/books/actions/create_book.py"
        ),
    ):
        assert isinstance(env.error, FieldNotSupportedError)
        assert env.node_file_is_unchanged()


class Env(TestEnv):
    pass
