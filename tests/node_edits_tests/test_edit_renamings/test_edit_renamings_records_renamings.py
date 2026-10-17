from groupy.renamings.actions.remove_renaming import remove_renaming
from groupy.renamings.actions.set_renaming import set_renaming
from node_edits_tests.node_edits_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_edit_renamings_records_renamings(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file.
    if env.step(
        env.create_module_with_node_file(),
    ):
        pass

    # We propose renamings for a module-level symbol, for a local symbol of
    # create_book, for a local symbol of the add_chapter method, and for an
    # attribute of the Book class.
    #
    # Each renaming should be recorded in the node of its scope.
    if env.step(
        env.edit_node_file(set_renaming, "@module", "API_URL", "BOOKS_API_URL"),
        env.edit_node_file(set_renaming, "create_book", "title", "book_title"),
        env.edit_node_file(set_renaming, "Book.add_chapter", "title", "chapter_title"),
        env.edit_node_file(set_renaming, "Book", "title", "name"),
        env.load_module_node(),
    ):
        assert env.module_node.renamings == {"API_URL": "BOOKS_API_URL"}
        assert env.function_node("create_book").renamings == {"title": "book_title"}
        assert env.method_node("Book", "add_chapter").renamings == {
            "title": "chapter_title"
        }
        assert env.class_node("Book").renamings == {"title": "name"}

    # We change the renaming in create_book, and remove the renaming in
    # add_chapter.
    #
    # The renaming in create_book should have the new name, and add_chapter
    # should have no renamings.
    if env.step(
        env.edit_node_file(set_renaming, "create_book", "title", "name"),
        env.edit_node_file(remove_renaming, "Book.add_chapter", "title"),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").renamings == {"title": "name"}
        assert env.method_node("Book", "add_chapter").renamings == {}
        # The edits only change the node file.
        assert env.module_is_unchanged()


class Env(TestEnv):
    pass
