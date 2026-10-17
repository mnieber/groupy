from groupy.nodes.utils.exceptions import AmbiguousLocationError, NodeNotFoundError
from node_edits_tests.node_edits_test_env import Context, TestEnv

LIBRARY_PY = """\
def validate(item):
    return item is not None


class Book:
    def validate(self):
        return bool(self.title)

    def save(self):
        pass


class Author:
    def save(self):
        pass
"""


def create_env(context: Context):
    return Env(context)


def test_find_node_rejects_unknown_and_ambiguous_locations(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a module in which two classes have a save method, and in which a
    # top-level function and a method are both called validate.
    if env.step(
        env.create_module_with_node_file("myapp/library.py", LIBRARY_PY),
        env.load_module_node(),
    ):
        pass

    # We find a function that does not exist, and a method that exists, but
    # not in the given class.
    #
    # Both should raise a NodeNotFoundError.
    if env.step(
        env.find_node_and_catch_error("create_book"),
    ):
        assert isinstance(env.error, NodeNotFoundError)

    if env.step(
        env.find_node_and_catch_error("Author.validate"),
    ):
        assert isinstance(env.error, NodeNotFoundError)

    # We find "save", which is the name of a method in two classes.
    #
    # It should raise an AmbiguousLocationError, since the location does not
    # say which class is meant.
    if env.step(
        env.find_node_and_catch_error("save"),
    ):
        assert isinstance(env.error, AmbiguousLocationError)

    # We find "Book.save".
    #
    # The class name should resolve the ambiguity.
    if env.step(
        env.find_node("Book.save"),
    ):
        assert env.found_node is env.method_node("Book", "save")

    # We find "validate", which is the full name of the top-level function and
    # the last part of the name of the Book.validate method.
    #
    # A location that is the full name of a node should find that node.
    if env.step(
        env.find_node("validate"),
    ):
        assert env.found_node is env.function_node("validate")


class Env(TestEnv):
    pass
