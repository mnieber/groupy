from breaker_sync_tests.breaker_sync_test_env import Context, TestEnv

# books.py after create_book was renamed to make_book, the publish method was
# added to Book, and MAX_CHAPTERS was replaced by DEFAULT_TITLE.
BOOKS_PY = """\
DEFAULT_TITLE = "Untitled"


class Book:
    def __init__(self, title):
        self.title = title

    def publish(self):
        pass


def make_book(title):
    return Book(_normalize_title(title))


def _normalize_title(title):
    return title.strip()
"""

AUTHORS_PY = """\
class Author:
    def __init__(self, name):
        self.name = name
"""


def create_env(context: Context):
    return Env(context)


def test_breaker_sync_updates_the_node_files(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, and create_book has a
    # responsibility.
    if env.step(
        env.create_session(),
        env.add_responsibility("myapp/books.py", "create_book", "Creates a book"),
        env.commit_all("add a responsibility"),
    ):
        pass

    # We run breaker sync.
    #
    # The node files reflect the source, so nothing should change.
    if env.step(
        env.run_breaker_sync(),
    ):
        assert env.output_lines == ["The node files match the source."]
        assert env.changed_files() == set()

    # We change books.py (a rename, an added method, and a removed and an
    # added variable), delete create_chapter.py and add authors.py, without
    # committing. Then we run breaker sync.
    #
    # Each change of the node files should be reported on a line, sorted by
    # module and location, followed by the request to review the changes. A
    # rename should be reported as a removed and an added node, and the
    # removed create_book should name the fields that it had.
    if env.step(
        env.write_file("src/myapp/books.py", BOOKS_PY),
        env.delete_file("src/myapp/chapters/create_chapter.py"),
        env.write_file("src/myapp/authors.py", AUTHORS_PY),
        env.remember_git_head(),
        env.run_breaker_sync(),
    ):
        assert env.output_lines == [
            "myapp/authors.py: created the node file",
            "myapp/books.py: added Book.publish",
            "myapp/books.py: added DEFAULT_TITLE",
            "myapp/books.py: removed MAX_CHAPTERS",
            "myapp/books.py: removed create_book (it had responsibilities)",
            "myapp/books.py: added make_book",
            "myapp/chapters/create_chapter.py: deleted the node file",
            "Please review the changes to the node files (e.g. with git diff), "
            "and move the analysis of renamed nodes.",
        ]

    # We look at the node file of books.py.
    #
    # It should reflect the new source. The new nodes should be in source
    # order among their siblings, and the line count should be updated.
    if env.step(
        env.load_module_node("myapp/books.py"),
    ):
        assert env.names(env.module_node.function_nodes) == [
            "make_book",
            "_normalize_title",
        ]
        assert env.names(env.class_node("Book").method_nodes) == [
            "__init__",
            "publish",
        ]
        assert env.names(env.module_node.variable_nodes) == ["DEFAULT_TITLE"]
        assert env.function_node("make_book").responsibilities == []
        assert env.module_node.line_count == len(BOOKS_PY.splitlines())

    # We look at the other node files.
    #
    # The node file of authors.py should have been created, the node file of
    # create_chapter.py should have been deleted, and the package node files
    # should list the modules of their package.
    if env.step(
        env.load_module_node("myapp/authors.py"),
    ):
        assert env.names(env.module_node.class_nodes) == ["Author"]
        assert not env.file_exists("src/myapp/chapters/create_chapter.py.breaker.yaml")

    if env.step(
        env.load_package_node("myapp"),
    ):
        assert env.package_node.module_names == [
            "myapp/__init__.py",
            "myapp/authors.py",
            "myapp/books.py",
        ]

    if env.step(
        env.load_package_node("myapp/chapters"),
    ):
        assert env.package_node.module_names == ["myapp/chapters/__init__.py"]

    # We look at the group file.
    #
    # authors.py should be in the group of the other modules in its dir, and
    # create_chapter.py should be gone.
    if env.step(
        env.load_groups(),
    ):
        assert env.module_names_per_group() == [
            ["myapp/__init__.py", "myapp/authors.py", "myapp/books.py"],
            ["myapp/chapters/__init__.py"],
        ]

    # We look at the repo.
    #
    # Breaker sync should not have committed, so that the developer can review
    # the changes.
    if env.step():
        assert env.git_head() == env.remembered_git_head
        assert env.changed_files() == {
            ".breaker/groups.txt",
            "src/myapp/authors.py",
            "src/myapp/authors.py.breaker.yaml",
            "src/myapp/books.py",
            "src/myapp/books.py.breaker.yaml",
            "src/myapp/chapters/create_chapter.py",
            "src/myapp/chapters/create_chapter.py.breaker.yaml",
            "src/myapp/chapters/package-node.breaker.yaml",
            "src/myapp/package-node.breaker.yaml",
        }


class Env(TestEnv):
    pass
