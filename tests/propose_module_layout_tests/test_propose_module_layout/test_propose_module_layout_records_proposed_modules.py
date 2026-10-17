from groupy.concepts.actions.set_concept import set_concept
from groupy.functions.actions.add_responsibility import add_responsibility
from groupy_next_tests.groupy_next_test_env import callback
from propose_module_layout_tests.propose_module_layout_test_env import (
    Context,
    TestEnv,
)

RFA_ID = "propose-module-layout/all"

BOOKS = "myapp/books.py"

GLOSSARY_YAML = """\
- name: book
  description: a written work that consists of chapters
"""

CALLBACKS = [
    callback(
        "set_proposed_module", name="myapp/books", description="Books and their titles"
    ),
    callback(
        "set_proposed_module", name="myapp/chapters", description="Chapters of books"
    ),
    callback("set_proposed_module", name="myapp/utils", description="Generic utils"),
    callback("remove_proposed_module", name="myapp/utils"),
]


def create_env(context: Context):
    return Env(context)


def test_propose_module_layout_records_proposed_modules(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-module-layout. The node file of books.py has a module concept,
    # and create_book has two responsibilities. The target code has a
    # glossary. The RFA proposes three feature packages, and then removes
    # one of them again.
    if env.step(
        env.create_session_at_propose_module_layout(),
        env.write_file("src/glossary.groupy.yaml", GLOSSARY_YAML),
        env.edit_node_file(set_concept, BOOKS, "@module", "book", "a written work"),
        env.edit_node_file(add_responsibility, BOOKS, "create_book", "Creates a book"),
        env.edit_node_file(
            add_responsibility, BOOKS, "create_book", "Normalizes the title"
        ),
        env.commit_all("analyze the code"),
        env.script_rfa(RFA_ID, *CALLBACKS),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should have made a single RFA for the whole code-base (which is
    # recorded as a finished chunk), committed after each callback, and
    # finished the stage.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.rfa_ids() == [RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            "propose-module-layout: set_proposed_module",
            "propose-module-layout: set_proposed_module",
            "propose-module-layout: set_proposed_module",
            "propose-module-layout: remove_proposed_module",
            "propose-module-layout: finish all",
            "propose-module-layout: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the context of the RFA.
    #
    # It should contain the glossary, and per module node file a summary
    # with the module concepts, and the top-level functions and classes with
    # their first responsibility (or None). Module-level variables are left
    # out.
    if env.step():
        rfa_context = env.rfa(RFA_ID).context
        assert rfa_context["glossary"] == GLOSSARY_YAML
        assert rfa_context["module_summaries"][BOOKS] == {
            "concepts": {"book": "a written work"},
            "code_units": {
                "Book": None,
                "create_book": "Creates a book",
                "_normalize_title": None,
            },
        }
        assert rfa_context["module_summaries"]["myapp/chapters/create_chapter.py"] == {
            "concepts": {},
            "code_units": {"create_chapter": None},
        }

    # We look at the root package node file.
    #
    # It should have the proposed modules.
    if env.step(
        env.load_root_package_node(),
    ):
        assert env.package_node.proposed_modules == {
            "myapp/books": "Books and their titles",
            "myapp/chapters": "Chapters of books",
        }

    # We look at the session.
    #
    # The next stage should be propose-code-restructure.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "propose-code-restructure"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
