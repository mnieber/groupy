from analyze_terminology_tests.analyze_terminology_test_env import (
    CONSOLIDATION_RFA_ID,
    Context,
    TestEnv,
    priority_callbacks,
)
from groupy_next_tests.fake_policies import UnscriptedRequestError

BOOKS_RFA_ID = "analyze-terminology/group-1/chunk-1"
CHAPTERS_RFA_ID = "analyze-terminology/group-2/chunk-1"


def create_env(context: Context):
    return Env(context)


def test_analyze_terminology_resumes_at_the_consolidation(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # analyze-terminology. With the package grouping strategy, myapp/books.py
    # and the modules of myapp/chapters are in different chunks. The RFAs of
    # both chunks are scripted, but the consolidation RFA is not.
    if env.step(
        env.create_session_at_analyze_terminology(),
        env.script_rfa(
            BOOKS_RFA_ID,
            *priority_callbacks(
                "myapp/books.py",
                "Book",
                "Book.__init__",
                "create_book",
                "_normalize_title",
            ),
        ),
        env.script_rfa(
            CHAPTERS_RFA_ID,
            *priority_callbacks("myapp/chapters/chapter_titles.py", "number_heading"),
            *priority_callbacks("myapp/chapters/create_chapter.py", "create_chapter"),
        ),
    ):
        pass

    # We run groupy next.
    #
    # The consolidation RFA has no script, so the fake policy should raise an
    # error, which interrupts the stage. Both chunks should be finished.
    if env.step(
        env.catch_error(env.run_groupy, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, UnscriptedRequestError)
        assert env.session.next_stage == "analyze-terminology"
        assert env.session.finished_chunks == [BOOKS_RFA_ID, CHAPTERS_RFA_ID]

    # We add a script for the consolidation RFA, and run groupy next again.
    #
    # It should only make the consolidation RFA, and then finish the stage.
    if env.step(
        env.script_rfa(CONSOLIDATION_RFA_ID),
        env.clear_rfa_requests(),
        env.remember_git_head(),
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.rfa_ids() == [CONSOLIDATION_RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            "analyze-terminology: finish consolidate-glossary",
            "analyze-terminology: finish the stage",
        ]
        assert env.session.next_stage == "propose-renamings"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
