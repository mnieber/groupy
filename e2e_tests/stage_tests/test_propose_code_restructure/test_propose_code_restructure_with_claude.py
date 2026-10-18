from stage_tests.e2e_test_env import Context, TestEnv

from groupy.package_nodes.actions.set_proposed_module import set_proposed_module

LIBRARY = "myapp/library.py"

LIBRARY_PY = """\
from dataclasses import dataclass

MAX_LOANS_PER_MEMBER = 3


@dataclass
class Book:
    title: str
    is_reference_only: bool = False
    borrower: str = None


def can_borrow_book(member_loans, book):
    return (
        len(member_loans) < MAX_LOANS_PER_MEMBER
        and not book.is_reference_only
        and book.borrower is None
    )


def borrow_book(member, member_loans, book):
    if not can_borrow_book(member_loans, book):
        raise ValueError(f"{member} cannot borrow {book.title}")
    book.borrower = member
    member_loans.append(book)
"""


def create_env(context: Context):
    return Env(context)


def test_propose_code_restructure_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is
    # propose-code-restructure. The module library.py has a model (Book), a
    # rule (can_borrow_book) and an action (borrow_book), and the proposed
    # modules have a package myapp/books. Haiku ignores the proposed modules
    # (e.g. it proposes myapp/models/book.py), so this test uses Sonnet.
    if env.step(
        env.create_session_with_claude({LIBRARY: LIBRARY_PY}, claude_model="sonnet"),
        env.edit_package_node_file(
            set_proposed_module, "myapp/books", "The books of the library"
        ),
        env.set_next_stage("propose-code-restructure"),
    ):
        pass

    # We run groupy next.
    #
    # Claude should have proposed a code restructure without problems, so
    # that the stage finished with a clean working tree.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "apply-code-restructure"
        assert env.git_status() == ""

    # We look at the node file of library.py.
    #
    # Claude should have recognized the model, the rule and the action, and
    # moved them to myapp/books.
    if env.step(
        env.load_module_node(LIBRARY),
    ):
        assert env.class_node("Book").code_unit_type == "model"
        assert env.function_node("can_borrow_book").code_unit_type == "rule"
        assert env.function_node("borrow_book").code_unit_type == "action"
        for node in [
            env.class_node("Book"),
            env.function_node("can_borrow_book"),
            env.function_node("borrow_book"),
        ]:
            assert node.move_to_file.startswith("myapp/books/"), node.name


class Env(TestEnv):
    pass
