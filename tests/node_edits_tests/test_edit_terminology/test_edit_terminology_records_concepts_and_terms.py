from node_edits_tests.node_edits_test_env import Context, TestEnv

from groupy.concepts.actions.add_alias import add_alias
from groupy.concepts.actions.remove_abbreviation import remove_abbreviation
from groupy.concepts.actions.remove_alias import remove_alias
from groupy.concepts.actions.remove_concept import remove_concept
from groupy.concepts.actions.remove_local_term import remove_local_term
from groupy.concepts.actions.set_abbreviation import set_abbreviation
from groupy.concepts.actions.set_concept import set_concept
from groupy.concepts.actions.set_local_term import set_local_term


def create_env(context: Context):
    return Env(context)


def test_edit_terminology_records_concepts_and_terms(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file.
    if env.step(
        env.create_module_with_node_file(),
    ):
        pass

    # We add two concepts to the module, one of them without a description.
    #
    # The module node should hold both concepts.
    if env.step(
        env.edit_node_file(
            set_concept, "@module", "book", "a written work that consists of chapters"
        ),
        env.edit_node_file(set_concept, "@module", "chapter", None),
        env.load_module_node(),
    ):
        assert env.module_node.concepts == {
            "book": "a written work that consists of chapters",
            "chapter": None,
        }

    # We add a concept and a local term to create_book, and a concept to the
    # Book class. Then we change the description of the concept of
    # create_book.
    #
    # The nodes should hold the concepts and the local term, with the latest
    # description.
    if env.step(
        env.edit_node_file(set_concept, "create_book", "title", "the name of a book"),
        env.edit_node_file(set_local_term, "create_book", "raw_title", None),
        env.edit_node_file(set_concept, "Book", "chapter_list", None),
        env.edit_node_file(
            set_concept, "create_book", "title", "the name on the cover of a book"
        ),
        env.load_module_node(),
    ):
        create_book_node = env.function_node("create_book")
        assert create_book_node.concepts == {"title": "the name on the cover of a book"}
        assert create_book_node.local_terms == {"raw_title": None}
        assert env.class_node("Book").concepts == {"chapter_list": None}

    # We add two aliases of "title" and an abbreviation to create_book.
    #
    # The aliases should be listed under the canonical name.
    if env.step(
        env.edit_node_file(add_alias, "create_book", "title", "name"),
        env.edit_node_file(add_alias, "create_book", "title", "book_title"),
        env.edit_node_file(set_abbreviation, "create_book", "maximum", "max"),
        env.load_module_node(),
    ):
        create_book_node = env.function_node("create_book")
        assert create_book_node.aliases == {"title": ["name", "book_title"]}
        assert create_book_node.abbreviations == {"maximum": "max"}

    # We remove a concept from the module, the local term and the abbreviation
    # from create_book, and one alias of "title".
    #
    # Only the removed entries should be gone.
    if env.step(
        env.edit_node_file(remove_concept, "@module", "chapter"),
        env.edit_node_file(remove_local_term, "create_book", "raw_title"),
        env.edit_node_file(remove_abbreviation, "create_book", "maximum"),
        env.edit_node_file(remove_alias, "create_book", "title", "name"),
        env.load_module_node(),
    ):
        create_book_node = env.function_node("create_book")
        assert list(env.module_node.concepts) == ["book"]
        assert create_book_node.local_terms == {}
        assert create_book_node.abbreviations == {}
        assert create_book_node.aliases == {"title": ["book_title"]}

    # We remove the last alias of "title".
    #
    # The canonical name should no longer be listed in the aliases.
    if env.step(
        env.edit_node_file(remove_alias, "create_book", "title", "book_title"),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").aliases == {}
        # The edits only change the node file.
        assert env.module_is_unchanged()


class Env(TestEnv):
    pass
