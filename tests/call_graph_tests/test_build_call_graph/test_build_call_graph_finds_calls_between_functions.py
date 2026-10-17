from call_graph_tests.call_graph_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_build_call_graph_finds_calls_between_functions(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the modules myapp/titles.py, myapp/books.py and myapp/authors.py.
    # Book and Author both have a save method.
    if env.step(
        env.write_myapp_modules(),
    ):
        pass

    # We build the call graph and load it.
    #
    # It should be stored in .groupy/call-graph.yaml.
    if env.step(
        env.build_call_graph(),
        env.load_call_graph(),
    ):
        assert (env.groupy_dir / "call-graph.yaml").exists()

    # We look at the calls within a module and between modules.
    #
    # Each call should be an edge between two functions or methods, named as
    # <file>:<qualified name>.
    if env.step():
        assert env.callees_of("myapp/titles.py:format_title") == {
            ("myapp/titles.py:capitalize", True)
        }
        # A call of a function that is imported from another module (by name,
        # or via its module) is a certain edge to that function.
        assert ("myapp/titles.py:format_title", True) in env.callees_of(
            "myapp/books.py:create_book"
        )
        assert env.callees_of("myapp/authors.py:Author.__init__") == {
            ("myapp/titles.py:capitalize", True)
        }

    # We look at the calls of classes and methods.
    #
    # A call of a class should be an edge to its __init__ method, and a call of
    # a method of self should be an edge to the method of the class.
    if env.step():
        assert env.callees_of("myapp/books.py:create_book") == {
            ("myapp/titles.py:format_title", True),
            ("myapp/books.py:Book.__init__", True),
        }
        assert env.callees_of("myapp/books.py:Book.save") == {
            ("myapp/books.py:Book._validate", True)
        }

    # We look at publish, which calls the save method of an item of unknown
    # type.
    #
    # There should be an uncertain edge to every save method in the target
    # code.
    if env.step():
        assert env.callees_of("myapp/authors.py:publish") == {
            ("myapp/books.py:Book.save", False),
            ("myapp/authors.py:Author.save", False),
        }

    # We look at the location of a call.
    #
    # The edge should record the file and the line of the call.
    if env.step():
        edge = env.edge("myapp/books.py:create_book", "myapp/titles.py:format_title")
        assert edge.file == "myapp/books.py"
        assert edge.line == env.line_of("myapp/books.py", "Book(format_title(title))")


class Env(TestEnv):
    pass
