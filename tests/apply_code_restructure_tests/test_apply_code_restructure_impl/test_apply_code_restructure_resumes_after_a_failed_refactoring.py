from apply_code_restructure_tests.apply_code_restructure_test_env import (
    CREATE_BOOK,
    CREATE_CHAPTER,
    NEW_CREATE_CHAPTER,
    Context,
    TestEnv,
)
from breaker_next_tests.fake_policies import FakeRefactoringError


def create_env(context: Context):
    return Env(context)


def test_apply_code_restructure_resumes_after_a_failed_refactoring(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-code-restructure, with a valid proposal for the modules of the
    # base env. The rename of create_chapter.py (in group-2) fails.
    if env.step(
        env.create_session_at_apply_code_restructure(),
        env.fail_refactoring(CREATE_CHAPTER, "@module"),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # The failed refactoring should interrupt the stage. books.py should have
    # been restructured and committed, and the working tree should be clean.
    if env.step(
        env.catch_error(env.run_breaker, "next"),
        env.load_session(),
    ):
        assert isinstance(env.error, FakeRefactoringError)
        assert env.commit_messages_since_remembered_head() == [
            "apply-code-restructure: restructure myapp/books.py",
            "apply-code-restructure: finish group-1/chunk-1",
        ]
        assert env.git_status() == ""
        assert env.module_exists(CREATE_BOOK)
        assert env.module_exists(CREATE_CHAPTER)
        assert env.session.next_stage == "apply-code-restructure"
        assert env.session.finished_chunks == ["apply-code-restructure/group-1/chunk-1"]

    # The refactoring no longer fails, and we run breaker next again.
    #
    # Breaker should only restructure create_chapter.py, and then finish the
    # stage.
    if env.step(
        env.clear_failing_refactorings(),
        env.clear_refactoring_calls(),
        env.remember_git_head(),
        env.run_breaker_next(),
        env.load_session(),
    ):
        assert env.refactoring_calls("move_module") == [(CREATE_CHAPTER, "@module")]
        assert env.refactoring_calls("move_symbol") == []
        assert env.commit_messages_since_remembered_head() == [
            "apply-code-restructure: restructure myapp/chapters/create_chapter.py",
            "apply-code-restructure: finish group-2/chunk-1",
            "apply-code-restructure: finish the stage",
        ]
        assert env.module_exists(NEW_CREATE_CHAPTER)
        assert env.session.next_stage == "done"


class Env(TestEnv):
    pass
