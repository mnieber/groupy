from groupy.restructure.actions.propose_code_restructure import (
    CodeRestructureHasProblemsError,
)
from groupy_next_tests.groupy_next_test_env import callback
from propose_code_restructure_tests.propose_code_restructure_test_env import (
    BOOKS_CALLBACKS,
    BOOKS_RFA_ID,
    CHAPTERS_CALLBACKS,
    CHAPTERS_RFA_ID,
    Context,
    TestEnv,
)

ZEBRA = "myapp/zebra.py"

CHAPTERS_RETRY_RFA_ID = "propose-code-restructure/group-2/chunk-1/retry-1"

ZEBRA_PY = """\
def create_chapter(title):
    return title
"""

# zebra.py (in group-1) moves its create_chapter to the file that group-2
# proposes for create_chapter of create_chapter.py.
ZEBRA_CALLBACKS = [
    callback(
        "set_code_unit_type",
        module_name=ZEBRA,
        location="create_chapter",
        code_unit_type="action",
    ),
    callback(
        "set_move_to_file",
        module_name=ZEBRA,
        location="create_chapter",
        move_to_file="myapp/chapters/actions/create_chapter.py",
    ),
]


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_rejects_a_clash_with_an_earlier_chunk(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-code-restructure. Besides the modules of the base env, myapp
    # has zebra.py, which is in group-1 (with books.py), although its path
    # sorts after the modules of myapp/chapters (group-2). The RFA of group-1
    # moves create_chapter of zebra.py to the file that the RFA of group-2
    # proposes for create_chapter of create_chapter.py. The follow-up RFA of
    # group-2 does nothing.
    if env.step(
        env.create_session_at_propose_code_restructure({ZEBRA: ZEBRA_PY}),
        env.script_rfa(BOOKS_RFA_ID, *BOOKS_CALLBACKS, *ZEBRA_CALLBACKS),
        env.script_rfa(CHAPTERS_RFA_ID, *CHAPTERS_CALLBACKS),
        env.script_rfa(CHAPTERS_RETRY_RFA_ID),
    ):
        pass

    # We run groupy next.
    #
    # The target file would receive two public code units. The clash should
    # be reported for the node of group-2, since the node of group-1 was
    # proposed in an earlier chunk.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, CodeRestructureHasProblemsError)
        assert (
            "myapp/chapters/create_chapter.py:create_chapter:"
            " myapp/chapters/actions/create_chapter.py already receives"
            " myapp/zebra.py:create_chapter" in str(env.error)
        )
        assert env.session.finished_chunks == [BOOKS_RFA_ID]


class Env(TestEnv):
    pass
