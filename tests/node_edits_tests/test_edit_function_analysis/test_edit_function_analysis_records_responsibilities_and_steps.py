from groupy.functions.actions.add_responsibility import add_responsibility
from groupy.functions.actions.add_step import add_step
from groupy.functions.actions.remove_responsibility import remove_responsibility
from groupy.functions.actions.remove_step import remove_step
from groupy.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)
from groupy.functions.actions.update_responsibility import update_responsibility
from groupy.functions.actions.update_step import update_step
from node_edits_tests.node_edits_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_edit_function_analysis_records_responsibilities_and_steps(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have the module myapp/books.py and its node file.
    if env.step(
        env.create_module_with_node_file(),
    ):
        pass

    # We add two responsibilities to create_book.
    #
    # They should be listed in the order in which they were added.
    if env.step(
        env.edit_node_file(add_responsibility, "create_book", "Creates a book"),
        env.edit_node_file(
            add_responsibility, "create_book", "Checks that the title is valid"
        ),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").responsibilities == [
            "Creates a book",
            "Checks that the title is valid",
        ]

    # We add three steps to create_book, and then insert a step before the
    # second step.
    #
    # The inserted step should be the second step.
    if env.step(
        env.edit_node_file(add_step, "create_book", "Format the title"),
        env.edit_node_file(add_step, "create_book", "Validate the title"),
        env.edit_node_file(add_step, "create_book", "Create the book"),
        env.edit_node_file(add_step, "create_book", "Log the title", 1),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").steps == [
            "Format the title",
            "Log the title",
            "Validate the title",
            "Create the book",
        ]

    # We update the second step and remove the first one.
    #
    # Steps should be identified by their index in the list.
    if env.step(
        env.edit_node_file(update_step, "create_book", 1, "Log the formatted title"),
        env.edit_node_file(remove_step, "create_book", 0),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").steps == [
            "Log the formatted title",
            "Validate the title",
            "Create the book",
        ]

    # We update the second responsibility and remove the first one.
    #
    # Responsibilities should be identified by their index in the list.
    if env.step(
        env.edit_node_file(
            update_responsibility, "create_book", 1, "Rejects an empty title"
        ),
        env.edit_node_file(remove_responsibility, "create_book", 0),
        env.load_module_node(),
    ):
        assert env.function_node("create_book").responsibilities == [
            "Rejects an empty title"
        ]

    # We add a responsibility to the Book class, and set the extract-method
    # priority of create_book and Book.
    #
    # Class nodes should also hold responsibilities and a priority.
    if env.step(
        env.edit_node_file(add_responsibility, "Book", "Holds the chapters of a book"),
        env.edit_node_file(set_extract_method_priority, "create_book", "high"),
        env.edit_node_file(set_extract_method_priority, "Book", "n/a"),
        env.load_module_node(),
    ):
        assert env.class_node("Book").responsibilities == [
            "Holds the chapters of a book"
        ]
        assert env.function_node("create_book").extract_method_priority == "high"
        assert env.class_node("Book").extract_method_priority == "n/a"
        # The edits only change the node file.
        assert env.module_is_unchanged()


class Env(TestEnv):
    pass
