from stage_tests.e2e_test_env import Context, TestEnv

from groupy.concepts.actions.set_concept import set_concept
from groupy.functions.actions.add_responsibility import add_responsibility

BOOKS = "myapp/books.py"

AUTHORS = "myapp/authors.py"

BOOKS_PY = """\
def create_book(title, author):
    return {"title": title, "author": author}


def find_books_by_title(books, title):
    return [book for book in books if book["title"] == title]
"""

AUTHORS_PY = """\
def create_author(name):
    return {"name": name}


def format_author_name(author):
    return author["name"].title()
"""

GLOSSARY_YAML = """\
- name: book
  description: a written work that the library keeps
- name: author
  description: a person who wrote one or more books
"""


def create_env(context: Context):
    return Env(context)


def test_propose_module_layout_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is
    # propose-module-layout. The modules books.py and authors.py each cover a
    # concept of the glossary, and their node files have the concepts and the
    # responsibilities that the module summaries are made of.
    if env.step(
        env.create_session_with_claude({BOOKS: BOOKS_PY, AUTHORS: AUTHORS_PY}),
        env.write_glossary(GLOSSARY_YAML),
        env.edit_node_file(set_concept, BOOKS, "@module", "book", None),
        env.edit_node_file(add_responsibility, BOOKS, "create_book", "Creates a book"),
        env.edit_node_file(
            add_responsibility, BOOKS, "find_books_by_title", "Finds books by title"
        ),
        env.edit_node_file(set_concept, AUTHORS, "@module", "author", None),
        env.edit_node_file(
            add_responsibility, AUTHORS, "create_author", "Creates an author"
        ),
        env.edit_node_file(
            add_responsibility,
            AUTHORS,
            "format_author_name",
            "Formats the name of an author",
        ),
        env.set_next_stage("propose-module-layout"),
    ):
        pass

    # We run groupy next.
    #
    # The stage should have finished with a clean working tree.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "propose-code-restructure"
        assert env.git_status() == ""

    # We look at the proposed modules.
    #
    # Claude should have proposed feature packages in myapp, with a package
    # for books and one for authors.
    if env.step(
        env.load_root_package_node(),
    ):
        names = list(env.package_node.proposed_modules)
        assert names
        assert all(name.startswith("myapp/") for name in names)
        assert any("book" in name for name in names)
        assert any("author" in name for name in names)


class Env(TestEnv):
    pass
