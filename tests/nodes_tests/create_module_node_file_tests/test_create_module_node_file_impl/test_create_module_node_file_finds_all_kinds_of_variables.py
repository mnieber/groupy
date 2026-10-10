from create_module_node_file_tests.module_node_test_env import Context, TestEnv

SCREEN_PY = """\
import os

TIMEOUT: int = 30
WIDTH, HEIGHT = 80, 24
default_title: str
DEBUG = os.environ.get("DEBUG") == "1"
DEBUG = DEBUG or TIMEOUT > 60


def get_area():
    area = WIDTH * HEIGHT
    return area


class Screen:
    columns = 80
"""


def create_env(context: Context):
    return Env(context)


def test_create_module_node_file_finds_all_kinds_of_variables(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a module that assigns module-level variables in several ways.
    if env.step(
        env.write_module("myapp/screen.py", SCREEN_PY),
    ):
        pass

    # We create the module node file.
    #
    # There should be a variable node for each module-level variable, in the
    # order in which the variables first appear.
    if env.step(
        env.create_module_node_file("myapp/screen.py"),
        env.load_module_node("myapp/screen.py"),
    ):
        # A tuple assignment creates a node per name, an annotation without a
        # value also declares a variable, and a variable that is assigned
        # twice gets one node.
        assert env.names(env.module_node.variable_nodes) == [
            "TIMEOUT",
            "WIDTH",
            "HEIGHT",
            "default_title",
            "DEBUG",
        ]
        # Local variables of functions and class attributes are not
        # module-level variables.
        assert "area" not in env.names(env.module_node.variable_nodes)
        assert "columns" not in env.names(env.module_node.variable_nodes)

    # We look at the variable nodes.
    #
    # Their proposals should still be empty.
    if env.step():
        for variable_node in env.module_node.variable_nodes:
            assert variable_node.rename_to is None
            assert variable_node.move_to_file is None


class Env(TestEnv):
    pass
