from groupy_next_tests.groupy_next_test_env import Context, TestEnv, callback

RFA_ID_1 = "identify-helper-functions/group-1/chunk-1"

RFA_ID_2 = "identify-helper-functions/group-2/chunk-1"


def create_env(context: Context):
    return Env(context)


def test_groupy_next_tags_the_start_of_a_stage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, with the package grouping
    # strategy (two chunks). The first stage is replaced by a fake stage that
    # makes an RFA per chunk. Only the RFA of the first chunk has a script.
    #
    # groupy init should have tagged its commit as groupy/init.
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
    ):
        assert env.git_tags() == {"groupy/init"}
        assert env.tagged_commit("groupy/init") == env.git_head()

    # We commit a review edit of the developer, and run groupy next.
    #
    # The stage should be interrupted at the second chunk. Groupy should have
    # tagged the start of the stage, after the review edit.
    if env.step(
        env.append_to_file("README.md", "Reviewed the node files.\n"),
        env.commit_all("review the node files"),
        env.remember_git_head(),
        env.run_groupy_and_catch_error("next"),
    ):
        assert env.error is not None
        assert env.git_tags() == {
            "groupy/init",
            "groupy/identify-helper-functions/start",
        }
        assert (
            env.tagged_commit("groupy/identify-helper-functions/start")
            == env.remembered_git_head
        )

    # We add a script for the second chunk, and run groupy next again.
    #
    # Groupy should resume the stage, and keep the tag at the start of the
    # stage. The next stage has not started, so it has no tag yet.
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
    ):
        assert env.git_tags() == {
            "groupy/init",
            "groupy/identify-helper-functions/start",
        }
        assert (
            env.tagged_commit("groupy/identify-helper-functions/start")
            == env.remembered_git_head
        )


class Env(TestEnv):
    pass
