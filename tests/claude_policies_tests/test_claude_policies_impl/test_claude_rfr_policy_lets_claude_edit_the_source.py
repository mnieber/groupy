from claude_policies_tests.claude_policies_test_env import (
    Context,
    TestEnv,
    run_callback,
    write_file,
)

RFR_ID = "apply-move-steps-to-caller/group-1/chunk-1"

BOOKS = "myapp/books.py"

NEW_BOOKS_PY = """\
MAX_CHAPTERS = 10


class Book:
    def __init__(self, title):
        self.title = title


def create_book(title):
    return Book(title.strip())
"""


def create_env(context: Context):
    return Env(context)


def test_claude_rfr_policy_lets_claude_edit_the_source(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses the Claude policies. In the RFR, the fake
    # claude edits books.py, adds a responsibility, tries to extract a method
    # (which is a refactoring callback), and commits the refactoring.
    if env.step(
        env.create_session_with_claude_policies(),
        env.script_claude(
            RFR_ID,
            write_file(f"src/{BOOKS}", NEW_BOOKS_PY),
            run_callback(
                "add_responsibility",
                module_name=BOOKS,
                location="create_book",
                responsibility="Creates a book",
            ),
            run_callback(
                "extract_method",
                module_name=BOOKS,
                location="create_book",
                new_name="strip_title",
                description="Strips the title",
            ),
            run_callback("commit_refactoring", description="inline the title"),
        ),
        env.remember_git_head(),
    ):
        pass

    # We run the RFR with the RFR policy.
    #
    # Claude may also edit files in an RFR, and the callbacks run in RFR mode.
    if env.step(
        env.run_rfr(RFR_ID),
    ):
        assert env.claude_option(RFR_ID, "--tools") == [
            "Read,Glob,Grep,Bash,Edit,Write"
        ]
        assert "Edit" in env.claude_option(RFR_ID, "--allowedTools")
        assert env.claude_record(RFR_ID)["env"]["GROUPY_IN_RFR"] == "1"

    # We look at the outputs of the callbacks, and at the commits.
    #
    # The node edit should not have committed, and extract_method should have
    # been rejected, with the offer to retry. commit_refactoring should have
    # committed the source and the node file together.
    if env.step():
        outputs = env.command_outputs(RFR_ID)
        assert outputs[0] == "OK\n"
        assert "CallbackNotAllowedError" in outputs[1]
        assert "retry it once" in outputs[1]
        assert outputs[2] == "OK\n"
        assert env.commit_messages_since_remembered_head() == [
            "identify-helper-functions: inline the title"
        ]
        assert env.files_in_head_commit() == {
            f"src/{BOOKS}",
            f"src/{BOOKS}.groupy.yaml",
        }
        assert env.git_status() == ""


class Env(TestEnv):
    pass
