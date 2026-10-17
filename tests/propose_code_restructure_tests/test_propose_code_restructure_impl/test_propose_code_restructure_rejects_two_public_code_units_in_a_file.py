from breaker.restructure.actions.propose_code_restructure import (
    CodeRestructureHasProblemsError,
)
from breaker_next_tests.breaker_next_test_env import callback
from propose_code_restructure_tests.propose_code_restructure_test_env import (
    BOOKS_RFA_ID,
    CHAPTERS_RFA_ID,
    REPORTS_RETRY_RFA_ID,
    REPORTS_RFA_ID,
    Context,
    TestEnv,
)

REPORT = "myapp/reports/report.py"

TARGET_FILE = "myapp/books/actions/create_book.py"

REPORT_PY = """\
LIMIT = 3


class TitleError(Exception):
    pass


def create_book(title):
    if not title:
        raise TitleError()
    return title
"""

# The RFA of the chunk moves a constant, an exception class and the action
# create_book to the file of the action create_book of books.py (which
# group-1 proposed as the new name of books.py).
CHUNK_CALLBACKS = [
    callback(
        "set_code_unit_type",
        module_name=REPORT,
        location="LIMIT",
        code_unit_type="constant",
    ),
    callback(
        "set_move_to_file",
        module_name=REPORT,
        location="LIMIT",
        move_to_file=TARGET_FILE,
    ),
    callback(
        "set_code_unit_type",
        module_name=REPORT,
        location="TitleError",
        code_unit_type="exception",
    ),
    callback(
        "set_move_to_file",
        module_name=REPORT,
        location="TitleError",
        move_to_file=TARGET_FILE,
    ),
    callback(
        "set_code_unit_type",
        module_name=REPORT,
        location="create_book",
        code_unit_type="action",
    ),
    callback(
        "set_move_to_file",
        module_name=REPORT,
        location="create_book",
        move_to_file=TARGET_FILE,
    ),
]


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_rejects_two_public_code_units_in_a_file(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-code-restructure. Besides the modules of the base env, myapp
    # has myapp/reports/report.py (in group-3), which also has a function
    # create_book. The RFAs of the base modules make a valid proposal. The
    # RFA of group-3 moves the code units of report.py to the file that
    # group-1 proposed for create_book of books.py, and the follow-up RFA
    # does nothing.
    if env.step(
        env.create_session_at_propose_code_restructure({REPORT: REPORT_PY}),
        env.script_base_modules(),
        env.script_rfa(REPORTS_RFA_ID, *CHUNK_CALLBACKS),
        env.script_rfa(REPORTS_RETRY_RFA_ID),
    ):
        pass

    # We run breaker next.
    #
    # The target file would receive two public code units (the action
    # create_book of books.py and of report.py), so Breaker should raise an
    # error, which interrupts the stage. The problem is reported for the node
    # of group-3, although the other node is in group-1. The constant and
    # the exception class may go to the file of an action, so they are not a
    # problem.
    if env.step(
        env.catch_error(env.run_breaker, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, CodeRestructureHasProblemsError)
        assert (
            "myapp/reports/report.py:create_book: myapp/books/actions/create_book.py"
            " already receives myapp/books.py:create_book" in str(env.error)
        )
        assert "LIMIT" not in str(env.error)
        assert "TitleError" not in str(env.error)
        assert env.git_status() == ""
        assert env.session.next_stage == "propose-code-restructure"
        assert env.session.finished_chunks == [BOOKS_RFA_ID, CHAPTERS_RFA_ID]


class Env(TestEnv):
    pass
