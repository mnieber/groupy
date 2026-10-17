from analyze_terminology_tests.analyze_terminology_test_env import (
    CONSOLIDATION_RFA_ID,
    Context,
    TestEnv,
    commit_messages,
    priority_callbacks,
)
from groupy.call_graph.enums import CallScopes
from groupy_next_tests.groupy_next_test_env import callback
from sessions_tests.groupy_test_env import BOOKS_PY

BOOKS_RFA_ID = "analyze-terminology/group-1/chunk-1"
CHAPTERS_RFA_ID = "analyze-terminology/group-2/chunk-1"

BOOKS = "myapp/books.py"
CHAPTER_TITLES = "myapp/chapters/chapter_titles.py"
CREATE_CHAPTER = "myapp/chapters/create_chapter.py"

# The callbacks of the RFA of the books chunk. They analyze books.py, and add
# the concepts book, title and chapter to the glossary.
BOOKS_CALLBACKS = [
    callback(
        "set_concept",
        module_name=BOOKS,
        location="@module",
        concept="book",
        description="a written work that consists of chapters",
    ),
    callback(
        "set_concept",
        module_name=BOOKS,
        location="create_book",
        concept="title",
        description="the name of a book",
    ),
    callback(
        "add_responsibility",
        module_name=BOOKS,
        location="create_book",
        responsibility="Creates a book with a normalized title",
    ),
    callback(
        "add_step",
        module_name=BOOKS,
        location="create_book",
        step="Normalize the title",
    ),
    callback(
        "add_step",
        module_name=BOOKS,
        location="create_book",
        step="Create the book",
    ),
    *priority_callbacks(
        BOOKS, "Book", "Book.__init__", "create_book", "_normalize_title"
    ),
    callback(
        "add_glossary_entry",
        name="book",
        description="a written work that consists of chapters",
    ),
    callback("add_glossary_entry", name="title", description="the name of a book"),
    callback("add_glossary_entry", name="chapter", description="a part of a book"),
]

# The callbacks of the RFA of the chapters chunk. They analyze the modules of
# myapp/chapters (including the abbreviation of a local term), add a second
# meaning of title to the glossary, and add section, which has the same
# meaning as chapter.
CHAPTERS_CALLBACKS = [
    callback(
        "set_concept",
        module_name=CHAPTER_TITLES,
        location="number_heading",
        concept="chapter_title",
        description="the heading of a chapter, with its number",
    ),
    callback(
        "set_local_term",
        module_name=CHAPTER_TITLES,
        location="number_heading",
        local_term="number",
        description=None,
    ),
    callback(
        "set_abbreviation",
        module_name=CHAPTER_TITLES,
        location="number_heading",
        term="number",
        abbreviation="nr",
    ),
    callback(
        "add_alias",
        module_name=CHAPTER_TITLES,
        location="number_heading",
        name="chapter_title",
        alias="heading",
    ),
    callback(
        "set_concept",
        module_name=CREATE_CHAPTER,
        location="create_chapter",
        concept="section",
        description="a part of a book",
    ),
    *priority_callbacks(CHAPTER_TITLES, "number_heading"),
    *priority_callbacks(CREATE_CHAPTER, "create_chapter"),
    callback(
        "add_glossary_entry", name="title", description="the heading of a chapter"
    ),
    callback("add_glossary_entry", name="section", description="a part of a book"),
]

# The callbacks of the consolidation RFA. They merge section into chapter.
CONSOLIDATION_CALLBACKS = [
    callback("merge_glossary_entries", name="section", into_name="chapter"),
]


def create_env(context: Context):
    return Env(context)


def test_analyze_terminology_fills_the_analysis_and_the_glossary(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # analyze-terminology. With the package grouping strategy, myapp/books.py
    # and the modules of myapp/chapters are in different chunks. The RFAs of
    # both chunks and the consolidation RFA are scripted.
    if env.step(
        env.create_session_at_analyze_terminology(),
        env.script_rfa(BOOKS_RFA_ID, *BOOKS_CALLBACKS),
        env.script_rfa(CHAPTERS_RFA_ID, *CHAPTERS_CALLBACKS),
        env.script_rfa(CONSOLIDATION_RFA_ID, *CONSOLIDATION_CALLBACKS),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should have made an RFA per chunk and then the consolidation
    # RFA, committing after each callback, after each chunk (also after the
    # consolidation) and after the stage.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.rfa_ids() == [BOOKS_RFA_ID, CHAPTERS_RFA_ID, CONSOLIDATION_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(BOOKS_CALLBACKS),
            "analyze-terminology: finish group-1/chunk-1",
            *commit_messages(CHAPTERS_CALLBACKS),
            "analyze-terminology: finish group-2/chunk-1",
            *commit_messages(CONSOLIDATION_CALLBACKS),
            "analyze-terminology: finish consolidate-glossary",
            "analyze-terminology: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the context of the RFA of the books chunk.
    #
    # It should contain the source of the modules of the chunk, the call graph
    # view (with the callers and callees) and the (still empty) glossary.
    if env.step():
        context = env.rfa(BOOKS_RFA_ID).context
        assert context["module_sources"] == {
            "myapp/__init__.py": "",
            "myapp/books.py": BOOKS_PY,
        }
        assert env.callees_in_context(BOOKS_RFA_ID, "myapp/books.py:create_book") == {
            ("myapp/books.py:Book.__init__", CallScopes.SAME_MODULE),
            ("myapp/books.py:_normalize_title", CallScopes.SAME_MODULE),
        }
        assert env.glossary_entries_in_context(BOOKS_RFA_ID) == []

    # We look at the glossary in the context of the later RFAs.
    #
    # Each RFA should receive the glossary so far.
    if env.step():
        assert env.glossary_entries_in_context(CHAPTERS_RFA_ID) == [
            ("book", "a written work that consists of chapters"),
            ("chapter", "a part of a book"),
            ("title", "the name of a book"),
        ]
        assert env.glossary_entries_in_context(CONSOLIDATION_RFA_ID) == [
            ("book", "a written work that consists of chapters"),
            ("chapter", "a part of a book"),
            ("section", "a part of a book"),
            ("title", "the name of a book"),
            ("title", "the heading of a chapter"),
        ]

    # We look at the glossary.
    #
    # It should have two entries for title (one per meaning), and section
    # should be merged into chapter.
    if env.step(
        env.load_glossary(),
    ):
        assert env.glossary_entries() == [
            ("book", "a written work that consists of chapters", []),
            ("chapter", "a part of a book", ["section"]),
            ("title", "the name of a book", []),
            ("title", "the heading of a chapter", []),
        ]

    # We look at the node file of books.py.
    #
    # The callbacks should have filled the analysis.
    if env.step(
        env.load_module_node(BOOKS),
    ):
        assert env.module_node.concepts == {
            "book": "a written work that consists of chapters"
        }
        create_book_node = env.function_node("create_book")
        assert create_book_node.concepts == {"title": "the name of a book"}
        assert create_book_node.responsibilities == [
            "Creates a book with a normalized title"
        ]
        assert create_book_node.steps == ["Normalize the title", "Create the book"]
        assert create_book_node.extract_method_priority == "n/a"

    # We look at the node file of chapter_titles.py.
    #
    # The callbacks should have filled the concepts, local terms, aliases and
    # abbreviations.
    if env.step(
        env.load_module_node(CHAPTER_TITLES),
    ):
        number_heading_node = env.function_node("number_heading")
        assert number_heading_node.concepts == {
            "chapter_title": "the heading of a chapter, with its number"
        }
        assert number_heading_node.local_terms == {"number": None}
        assert number_heading_node.aliases == {"chapter_title": ["heading"]}
        assert number_heading_node.abbreviations == {"number": "nr"}

    # We look at the session.
    #
    # The next stage should be propose-renamings.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "propose-renamings"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
