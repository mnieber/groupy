from create_module_node_file_tests.module_node_test_env import Context, TestEnv

CONSTANTS_PY = '''\
"""Re-exports the constants of the app."""

from myapp.settings import MAX_CHAPTERS
'''


def create_env(context: Context):
    return Env(context)


def test_create_module_node_file_for_a_module_without_definitions(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have an empty module, and a module that only has a docstring and an
    # import.
    if env.step(
        env.write_module("myapp/empty.py", ""),
        env.write_module("myapp/constants.py", CONSTANTS_PY),
    ):
        pass

    # We create the module node file for the empty module.
    #
    # The node file should still be created, without nodes and with a line
    # count of zero.
    if env.step(
        env.create_module_node_file("myapp/empty.py"),
        env.load_module_node("myapp/empty.py"),
    ):
        assert env.file_exists("myapp/empty.py.groupy.yaml")
        assert env.module_node.line_count == 0
        assert env.module_node.function_nodes == []
        assert env.module_node.class_nodes == []
        assert env.module_node.variable_nodes == []

    # We create the module node file for the module with the docstring and
    # the import.
    #
    # The node file should have no nodes.
    if env.step(
        env.create_module_node_file("myapp/constants.py"),
        env.load_module_node("myapp/constants.py"),
    ):
        assert env.module_node.line_count == 3
        assert env.module_node.function_nodes == []
        assert env.module_node.class_nodes == []
        assert env.module_node.variable_nodes == []


class Env(TestEnv):
    pass
