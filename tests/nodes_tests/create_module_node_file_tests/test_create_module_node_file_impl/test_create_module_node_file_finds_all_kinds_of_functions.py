from create_module_node_file_tests.module_node_test_env import Context, TestEnv

LIBRARY_PY = """\
import functools
from dataclassy import dataclass


@dataclass
class Library:
    name: str

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return self.name.lower()

    @staticmethod
    def create(name):
        return Library(name=name)

    async def fetch_books(self):
        return []


@functools.cache
def get_default_library():
    return Library.create("default")


async def sync_library(library):
    def _log_progress(step):
        def _format_step():
            return f"step {step}"

        print(_format_step())

    _log_progress(1)
    await library.fetch_books()
"""


def create_env(context: Context):
    return Env(context)


def test_create_module_node_file_finds_all_kinds_of_functions(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a module with decorated and async functions and methods, and
    # with functions that are nested in the code two levels deep.
    if env.step(
        env.write_module("myapp/library.py", LIBRARY_PY),
    ):
        pass

    # We create the module node file.
    #
    # Decorated and async functions should have a function node, and a
    # decorated class should have a class node.
    if env.step(
        env.create_module_node_file("myapp/library.py"),
        env.load_module_node("myapp/library.py"),
    ):
        assert env.names(env.module_node.function_nodes) == [
            "get_default_library",
            "sync_library",
        ]
        assert env.names(env.module_node.class_nodes) == ["Library"]

    # We look at the methods of Library.
    #
    # Dunder methods, properties, static methods and async methods should all
    # have a method node.
    if env.step():
        assert env.names(env.class_node("Library").method_nodes) == [
            "__str__",
            "slug",
            "create",
            "fetch_books",
        ]

    # We look at the function nodes of sync_library.
    #
    # The functions that are nested in sync_library are part of its body, at
    # any depth, so they should have no nodes.
    if env.step():
        assert env.function_node("sync_library").helper_function_nodes == []
        assert "_log_progress" not in env.names(env.module_node.function_nodes)
        assert "_format_step" not in env.names(env.module_node.function_nodes)


class Env(TestEnv):
    pass
