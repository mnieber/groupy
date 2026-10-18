from groupy_next_tests.groupy_next_test_env import callback
from groupy_status_tests.groupy_status_test_env import Context, TestEnv

RFA_ID_1 = "identify-helper-functions/group-1/chunk-1"

RFA_ID_2 = "identify-helper-functions/group-2/chunk-1"


def create_env(context: Context):
    return Env(context)


def test_groupy_status_reports_the_progress_of_the_session(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package (in the src dir), with the
    # package grouping strategy, so that the modules of myapp (group 1) and of
    # myapp/chapters (group 2) are in different chunks. The first stage is
    # replaced by a fake stage that makes an RFA per chunk. Only the RFA of the
    # first chunk has a script.
    if env.step(
        env.create_session(
            grouping_strategy="package", max_group_lines=10000, max_chunk_lines=10000
        ),
        env.install_fake_stage(),
        env.script_rfa(
            RFA_ID_1,
            callback(
                "add_responsibility",
                module_name="myapp/books.py",
                location="create_book",
                responsibility="Creates a book",
            ),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run groupy status.
    #
    # It should print the target dir, and that groupy next will start the
    # first stage. Nothing should have changed.
    if env.step(
        env.run_groupy_cli("status"),
    ):
        assert env.exit_code == 0
        assert env.output_contains("src", "identify-helper-functions", "will start")
        assert "will resume" not in env.output
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""

    # We run groupy next, which is interrupted at the second chunk, and then
    # groupy status.
    #
    # It should print that the last run was interrupted (with the request id
    # and the error), that groupy next will resume the stage, and which chunks
    # are finished and which remain.
    if env.step(
        env.run_groupy_and_catch_error("next"),
        env.remember_git_head(),
        env.run_groupy_cli("status"),
    ):
        assert env.exit_code == 0
        assert env.output_contains(
            "interrupted",
            RFA_ID_2,
            "UnscriptedRequestError",
            "will resume",
            "group-1/chunk-1",
            "group-2/chunk-1",
        )
        assert env.git_head() == env.remembered_git_head
        assert env.git_status() == ""

    # We add a script for the second chunk, run groupy next again, and then
    # groupy status.
    #
    # It should print that the last run finished the stage, what to review
    # for that stage, and that groupy next will start the next stage.
    if env.step(
        env.script_rfa(
            RFA_ID_2,
            callback(
                "add_responsibility",
                module_name="myapp/chapters/create_chapter.py",
                location="create_chapter",
                responsibility="Creates a chapter",
            ),
        ),
        env.run_groupy("next"),
        env.run_groupy_cli("status"),
    ):
        assert env.exit_code == 0
        assert env.output_contains(
            "finished",
            "helper_function_nodes",
            "analyze-terminology",
            "will start",
        )


class Env(TestEnv):
    pass
