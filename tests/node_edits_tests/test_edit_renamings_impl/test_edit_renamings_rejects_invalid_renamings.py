from groupy.nodes.utils.exceptions import (
    EntryNotFoundError,
    FieldNotSupportedError,
    InvalidValueError,
)
from groupy.renamings.actions.remove_renaming import remove_renaming
from groupy.renamings.actions.set_renaming import set_renaming
from node_edits_tests.node_edits_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_edit_renamings_rejects_invalid_renamings(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file.
    if env.step(
        env.create_module_with_node_file(),
        env.remember_node_file(),
    ):
        pass

    # We remove a renaming that create_book does not have.
    #
    # It should raise an EntryNotFoundError and leave the node file unchanged.
    if env.step(
        env.edit_node_file_and_catch_error(remove_renaming, "create_book", "title"),
    ):
        assert isinstance(env.error, EntryNotFoundError)
        assert env.node_file_is_unchanged()

    # We rename a symbol to its own name, and we rename create_book in its own
    # renamings.
    #
    # Each should raise an InvalidValueError.
    if env.step(
        env.edit_node_file_and_catch_error(
            set_renaming, "create_book", "title", "title"
        ),
    ):
        assert isinstance(env.error, InvalidValueError)

    if env.step(
        env.edit_node_file_and_catch_error(
            set_renaming, "create_book", "create_book", "create_new_book"
        ),
    ):
        # A renaming of the function itself is proposed with set_rename_to.
        assert isinstance(env.error, InvalidValueError)
        assert env.node_file_is_unchanged()

    # We add a renaming to the MAX_CHAPTERS variable.
    #
    # A variable node has no renamings, so it should raise a
    # FieldNotSupportedError.
    if env.step(
        env.edit_node_file_and_catch_error(
            set_renaming, "MAX_CHAPTERS", "MAX_CHAPTERS", "MAX_NR_OF_CHAPTERS"
        ),
    ):
        assert isinstance(env.error, FieldNotSupportedError)
        assert env.node_file_is_unchanged()


class Env(TestEnv):
    pass
