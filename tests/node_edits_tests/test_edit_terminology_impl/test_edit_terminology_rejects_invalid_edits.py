from groupy.concepts.actions.add_alias import add_alias
from groupy.concepts.actions.remove_alias import remove_alias
from groupy.concepts.actions.remove_concept import remove_concept
from groupy.concepts.actions.set_abbreviation import set_abbreviation
from groupy.concepts.actions.set_concept import set_concept
from groupy.concepts.actions.set_local_term import set_local_term
from groupy.nodes.utils.exceptions import EntryNotFoundError, FieldNotSupportedError
from node_edits_tests.node_edits_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_edit_terminology_rejects_invalid_edits(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file, in which "title"
    # has the alias "name" in create_book.
    if env.step(
        env.create_module_with_node_file(),
        env.edit_node_file(add_alias, "create_book", "title", "name"),
        env.remember_node_file(),
    ):
        pass

    # We remove a concept that the module does not have, and an alias that
    # create_book does not have.
    #
    # Each should raise an EntryNotFoundError and leave the node file
    # unchanged, so that a typo does not go unnoticed.
    if env.step(
        env.edit_node_file_and_catch_error(remove_concept, "@module", "author"),
    ):
        assert isinstance(env.error, EntryNotFoundError)

    if env.step(
        env.edit_node_file_and_catch_error(
            remove_alias, "create_book", "title", "label"
        ),
    ):
        assert isinstance(env.error, EntryNotFoundError)
        assert env.node_file_is_unchanged()

    # We add a local term to the Book class, a concept to the MAX_CHAPTERS
    # variable, and an abbreviation to the module.
    #
    # These nodes do not have these fields, so each should raise a
    # FieldNotSupportedError.
    if env.step(
        env.edit_node_file_and_catch_error(set_local_term, "Book", "raw_title", None),
    ):
        assert isinstance(env.error, FieldNotSupportedError)

    if env.step(
        env.edit_node_file_and_catch_error(
            set_concept, "MAX_CHAPTERS", "chapter", None
        ),
    ):
        assert isinstance(env.error, FieldNotSupportedError)

    if env.step(
        env.edit_node_file_and_catch_error(
            set_abbreviation, "@module", "maximum", "max"
        ),
    ):
        assert isinstance(env.error, FieldNotSupportedError)
        assert env.node_file_is_unchanged()

    # We add the alias "name" of "title" a second time.
    #
    # The alias should be listed once.
    if env.step(
        env.edit_node_file(add_alias, "create_book", "title", "name"),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").aliases == {"title": ["name"]}


class Env(TestEnv):
    pass
