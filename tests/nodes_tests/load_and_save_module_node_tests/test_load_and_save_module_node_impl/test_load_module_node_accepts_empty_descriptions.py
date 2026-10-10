from load_and_save_module_node_tests.node_file_test_env import Context, TestEnv

# A node file that is edited by hand: the developer used "" and {} where Breaker
# would write null or leave the field out.
BOOKS_NODE_YAML = """\
module_node:
  name: myapp/books.py
  line_count: 12
  concepts:
    book: ""
  renamings: {}
  function_nodes:
    - name: create_book
      concepts:
        title: ''
        author: a person who wrote a book
      helper_function_nodes: []
"""

# The same node file, in the format that Breaker writes.
BOOKS_NODE_YAML_AS_SAVED = """\
module_node:
  name: myapp/books.py
  line_count: 12
  concepts:
    book: null
  function_nodes:
    - name: create_book
      concepts:
        title: null
        author: a person who wrote a book
"""


def create_env(context: Context):
    return Env(context)


def test_load_module_node_accepts_empty_descriptions(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a hand-edited node file with empty descriptions.
    if env.step(
        env.write_file("myapp/books.py.breaker.yaml", BOOKS_NODE_YAML),
    ):
        pass

    # We load the node file.
    #
    # An empty description should be loaded as None.
    if env.step(
        env.load_module_node("myapp/books.py.breaker.yaml"),
    ):
        assert env.module_node.concepts == {"book": None}
        assert env.module_node.function_nodes[0].concepts == {
            "title": None,
            "author": "a person who wrote a book",
        }

    # We save the module node to the same node file.
    #
    # The node file should be in the format that Breaker writes: an empty
    # description is written as null, and empty fields are left out.
    if env.step(
        env.save_module_node("myapp/books.py.breaker.yaml"),
    ):
        assert env.read_file("myapp/books.py.breaker.yaml") == (
            BOOKS_NODE_YAML_AS_SAVED
        )


class Env(TestEnv):
    pass
