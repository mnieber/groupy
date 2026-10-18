from node_edits_tests.node_edits_test_env import Context, TestEnv

from groupy.nodes.actions.set_code_unit_type import set_code_unit_type
from groupy.nodes.actions.set_move_to_file import set_move_to_file
from groupy.nodes.actions.set_rename_to import set_rename_to


def create_env(context: Context):
    return Env(context)


def test_set_node_fields_proposes_a_new_structure(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file.
    if env.step(
        env.create_module_with_node_file(),
    ):
        pass

    # We propose to rename create_book, to move it to an action file, and to
    # make it an action.
    #
    # The function node should hold the proposal.
    if env.step(
        env.edit_node_file(set_rename_to, "create_book", "create_new_book"),
        env.edit_node_file(
            set_move_to_file,
            "create_book",
            "myapp/books/actions/create_new_book.py",
        ),
        env.edit_node_file(set_code_unit_type, "create_book", "action"),
        env.load_module_node(),
    ):
        create_book_node = env.function_node("create_book")
        assert create_book_node.rename_to == "create_new_book"
        assert create_book_node.move_to_file == (
            "myapp/books/actions/create_new_book.py"
        )
        assert create_book_node.code_unit_type == "action"

    # We propose to move Book to a model file, and to make add_chapter a rule.
    #
    # The class node and the method node should hold the proposal.
    if env.step(
        env.edit_node_file(set_code_unit_type, "Book", "model"),
        env.edit_node_file(set_move_to_file, "Book", "myapp/books/models/book.py"),
        env.edit_node_file(set_code_unit_type, "Book.add_chapter", "rule"),
        env.load_module_node(),
    ):
        assert env.class_node("Book").code_unit_type == "model"
        assert env.class_node("Book").move_to_file == "myapp/books/models/book.py"
        assert env.method_node("Book", "add_chapter").code_unit_type == "rule"

    # We propose to keep MAX_CHAPTERS as a constant under a new name, and to
    # move API_URL to the settings.
    #
    # The variable nodes should hold the proposal.
    if env.step(
        env.edit_node_file(set_code_unit_type, "MAX_CHAPTERS", "constant"),
        env.edit_node_file(set_rename_to, "MAX_CHAPTERS", "MAX_NR_OF_CHAPTERS"),
        env.edit_node_file(set_code_unit_type, "API_URL", "setting"),
        env.edit_node_file(set_move_to_file, "API_URL", "myapp/settings.py"),
        env.load_module_node(),
    ):
        assert env.variable_node("MAX_CHAPTERS").code_unit_type == "constant"
        assert env.variable_node("MAX_CHAPTERS").rename_to == "MAX_NR_OF_CHAPTERS"
        assert env.variable_node("API_URL").code_unit_type == "setting"
        assert env.variable_node("API_URL").move_to_file == "myapp/settings.py"

    # We propose a new path for the module.
    #
    # The module node should hold the proposal.
    if env.step(
        env.edit_node_file(
            set_rename_to, "@module", "myapp/books/actions/create_new_book.py"
        ),
        env.load_module_node(),
    ):
        assert env.module_node.rename_to == "myapp/books/actions/create_new_book.py"

    # We change our mind: create_book stays in the current file.
    #
    # Setting a field to None should clear it.
    if env.step(
        env.edit_node_file(set_move_to_file, "create_book", None),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").move_to_file is None
        # The edits only change the node file.
        assert env.module_is_unchanged()


class Env(TestEnv):
    pass
