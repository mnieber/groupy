from apply_renamings_tests.apply_renamings_test_env import Context, TestEnv
from groupy.concepts.actions.set_concept import set_concept
from groupy.concepts.actions.set_local_term import set_local_term
from groupy.renamings.actions.set_renaming import set_renaming

HEADINGS = "myapp/headings.py"

HEADINGS_PY = """\
def format_heading(title, text):
    body = text.strip()
    return title + ": " + body
"""

RENAMED_HEADINGS_PY = """\
def format_heading(text, body):
    content = body.strip()
    return text + ": " + content
"""


def create_env(context: Context):
    return Env(context)


def test_apply_renamings_orders_chains_and_renames_keys(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-renamings. Besides the modules of the base env, myapp has
    # headings.py. The renamings of format_heading form a chain
    # (title -> text, text -> body, body -> content). It also renames the
    # concept chapter_heading to heading, which is already a concept of
    # format_heading. text and body are local terms.
    if env.step(
        env.create_session_at_apply_renamings({HEADINGS: HEADINGS_PY}),
        env.edit_node_file(
            set_concept, HEADINGS, "format_heading", "heading", "the title of a chapter"
        ),
        env.edit_node_file(
            set_concept, HEADINGS, "format_heading", "chapter_heading", "a heading"
        ),
        env.edit_node_file(set_local_term, HEADINGS, "format_heading", "text", None),
        env.edit_node_file(set_local_term, HEADINGS, "format_heading", "body", None),
        env.edit_node_file(set_renaming, HEADINGS, "format_heading", "title", "text"),
        env.edit_node_file(set_renaming, HEADINGS, "format_heading", "text", "body"),
        env.edit_node_file(set_renaming, HEADINGS, "format_heading", "body", "content"),
        env.edit_node_file(
            set_renaming, HEADINGS, "format_heading", "chapter_heading", "heading"
        ),
        env.commit_all("review the renamings"),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should have applied the chain in an order that works (body
    # first, title last). chapter_heading is not a symbol, so it should not
    # have been renamed in the source.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.read_module(HEADINGS) == RENAMED_HEADINGS_PY
        assert env.renamed_names() == [
            (HEADINGS, "body"),
            (HEADINGS, "text"),
            (HEADINGS, "title"),
        ]

    # We look at the node file of headings.py.
    #
    # The keys of the concepts and local terms should be renamed all at once,
    # so that text becomes body and body becomes content. The existing
    # concept heading should keep its own description.
    if env.step(
        env.load_module_node(HEADINGS),
    ):
        format_heading_node = env.function_node("format_heading")
        assert format_heading_node.concepts == {"heading": "the title of a chapter"}
        assert format_heading_node.local_terms == {"body": None, "content": None}
        assert format_heading_node.renamings == {}


class Env(TestEnv):
    pass
