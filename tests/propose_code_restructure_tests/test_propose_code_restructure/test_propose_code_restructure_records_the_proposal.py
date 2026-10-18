from propose_code_restructure_tests.propose_code_restructure_test_env import (
    BOOKS,
    BOOKS_CALLBACKS,
    BOOKS_RFA_ID,
    CHAPTERS_CALLBACKS,
    CHAPTERS_RFA_ID,
    CREATE_CHAPTER,
    PROPOSED_MODULES,
    Context,
    TestEnv,
    commit_messages,
)
from sessions_tests.groupy_test_env import BOOKS_PY

from groupy.call_graph.enums import CallScopes


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_records_the_proposal(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-code-restructure, and whose root package node file has the
    # proposed modules. _normalize_title is a helper function of create_book.
    # With the package grouping strategy, books.py is in group-1 and the
    # modules of myapp/chapters are in group-2. The RFA of each chunk
    # proposes where the code units go.
    if env.step(
        env.create_session_at_propose_code_restructure(),
        env.script_base_modules(),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should have made an RFA per chunk, committed after each
    # callback, and finished the chunks and the stage. The proposal follows
    # the dependency direction, so Groupy should say so.
    if env.step(
        env.run_groupy_next(),
    ):
        assert env.rfa_ids() == [BOOKS_RFA_ID, CHAPTERS_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(BOOKS_CALLBACKS),
            "propose-code-restructure: finish group-1/chunk-1",
            *commit_messages(CHAPTERS_CALLBACKS),
            "propose-code-restructure: finish group-2/chunk-1",
            "propose-code-restructure: finish the stage",
        ]
        assert env.git_status() == ""
        assert env.output_lines == [
            "The proposed code structure follows the dependency direction."
        ]

    # We look at the context of the RFA of books.py.
    #
    # It should contain the source of the modules of the chunk, the proposed
    # modules, the call graph view and the glossary.
    if env.step():
        rfa_context = env.rfa(BOOKS_RFA_ID).context
        assert rfa_context["module_sources"][BOOKS] == BOOKS_PY
        assert rfa_context["proposed_modules"] == PROPOSED_MODULES
        assert env.callees_in_context(BOOKS_RFA_ID, "myapp/books.py:create_book") == {
            ("myapp/books.py:Book.__init__", CallScopes.SAME_MODULE),
            ("myapp/books.py:_normalize_title", CallScopes.SAME_MODULE),
        }
        assert rfa_context["glossary"] == ""

    # We look at the node file of books.py.
    #
    # It should have the proposal. The helper function _normalize_title
    # moves with create_book, so it needs no code_unit_type.
    if env.step(
        env.load_module_node(BOOKS),
    ):
        assert env.module_node.rename_to == "myapp/books/actions/create_book.py"
        assert env.function_node("create_book").code_unit_type == "action"
        assert env.function_node("create_book._normalize_title").code_unit_type is None
        assert env.variable_node("MAX_CHAPTERS").code_unit_type == "constant"
        assert env.class_node("Book").code_unit_type == "model"
        assert env.class_node("Book").move_to_file == "myapp/books/models/book.py"

    # We look at the node file of create_chapter.py and at the source.
    #
    # The node file should have the proposal, and the source should be
    # unchanged, so that the developer can review the proposal.
    if env.step(
        env.load_module_node(CREATE_CHAPTER),
    ):
        assert env.module_node.rename_to == "myapp/chapters/actions/create_chapter.py"
        assert env.function_node("create_chapter").code_unit_type == "action"
        assert env.read_module(BOOKS) == BOOKS_PY

    # We look at the session.
    #
    # The next stage should be apply-code-restructure.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "apply-code-restructure"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
