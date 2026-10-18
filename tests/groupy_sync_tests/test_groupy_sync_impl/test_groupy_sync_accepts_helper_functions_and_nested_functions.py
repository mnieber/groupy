from groupy_sync_tests.groupy_sync_test_env import Context, TestEnv

AUTHORS_PY = """\
class Author:
    def __init__(self, name):
        self.name = name

    def save(self):
        _check_name(self)


def _check_name(author):
    def is_blank(text):
        return not text.strip()

    assert not is_blank(author.name)
"""


def create_env(context: Context):
    return Env(context)


def test_groupy_sync_accepts_helper_functions_and_nested_functions(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, which also has authors.py. The
    # _check_name function of authors.py contains the nested function
    # is_blank.
    if env.step(
        env.create_repo_with_target_code(),
        env.write_file("src/myapp/authors.py", AUTHORS_PY),
        env.commit_all("add authors"),
        env.run_groupy("init", "--accept-risks", "--target-dir=src"),
    ):
        pass

    # In the node files, we nest _normalize_title under the create_book
    # function, and _check_name under the save method of Author. Then we run
    # groupy sync.
    #
    # In the source, helper functions are top-level functions, and nested
    # functions have no node, so there should be no differences.
    if env.step(
        env.move_function_to_parent(
            "myapp/books.py", "_normalize_title", "create_book"
        ),
        env.move_function_to_parent("myapp/authors.py", "_check_name", "Author.save"),
        env.run_groupy_sync(),
    ):
        assert env.output_lines == ["The node files match the source."]


class Env(TestEnv):
    pass
