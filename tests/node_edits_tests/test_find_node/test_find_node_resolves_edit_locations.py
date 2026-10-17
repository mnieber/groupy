from groupy.functions.actions.move_function_to_parent import (
    move_function_to_parent,
)
from groupy.nodes.models.class_node import ClassNode
from groupy.nodes.models.function_node import FunctionNode
from groupy.nodes.models.module_node import ModuleNode
from groupy.nodes.models.variable_node import VariableNode
from node_edits_tests.node_edits_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_find_node_resolves_edit_locations(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file, in which _validate
    # is a helper function of create_book.
    if env.step(
        env.create_module_with_node_file(),
        env.edit_node_file(move_function_to_parent, "_validate", "create_book"),
        env.load_module_node(),
    ):
        pass

    # We find the node at "@module".
    #
    # It should be the module node.
    if env.step(
        env.find_node("@module"),
    ):
        assert isinstance(env.found_node, ModuleNode)
        assert env.found_node.name == "myapp/books.py"

    # We find the nodes of a top-level function, a class and a variable.
    #
    # They should be found by their name.
    if env.step(
        env.find_node("create_book"),
    ):
        assert isinstance(env.found_node, FunctionNode)
        assert env.found_node.name == "create_book"

    if env.step(
        env.find_node("Book"),
    ):
        assert isinstance(env.found_node, ClassNode)
        assert env.found_node.name == "Book"

    if env.step(
        env.find_node("MAX_CHAPTERS"),
    ):
        assert isinstance(env.found_node, VariableNode)
        assert env.found_node.name == "MAX_CHAPTERS"

    # We find the node of the add_chapter method, with and without the name of
    # its class.
    #
    # Both should find the method node.
    if env.step(
        env.find_node("Book.add_chapter"),
    ):
        assert isinstance(env.found_node, FunctionNode)
        assert env.found_node is env.method_node("Book", "add_chapter")

    if env.step(
        env.find_node("add_chapter"),
    ):
        assert env.found_node is env.method_node("Book", "add_chapter")

    # We find the node of the helper function _validate, with and without the
    # name of its parent function.
    #
    # Both should find the helper function node.
    if env.step(
        env.find_node("create_book._validate"),
    ):
        assert env.found_node.name == "_validate"
        assert env.found_node is (
            env.function_node("create_book").helper_function_nodes[0]
        )

    if env.step(
        env.find_node("_validate"),
    ):
        assert env.found_node is (
            env.function_node("create_book").helper_function_nodes[0]
        )


class Env(TestEnv):
    pass
