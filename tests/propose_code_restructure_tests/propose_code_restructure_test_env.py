import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv
from groupy_next_tests.groupy_next_test_env import callback

from groupy.claude_requests.models.callback import Callback
from groupy.functions.actions.move_function_to_parent import move_function_to_parent
from groupy.nodes.actions.set_proposed_module import set_proposed_module

__all__ = ["Context", "TestEnv"]

STAGE = "propose-code-restructure"

BOOKS = "myapp/books.py"
CREATE_CHAPTER = "myapp/chapters/create_chapter.py"

BOOKS_RFA_ID = "propose-code-restructure/group-1/chunk-1"
CHAPTERS_RFA_ID = "propose-code-restructure/group-2/chunk-1"
# The RFA of the modules that a test adds in myapp/reports.
REPORTS_RFA_ID = "propose-code-restructure/group-3/chunk-1"
REPORTS_RETRY_RFA_ID = "propose-code-restructure/group-3/chunk-1/retry-1"

PROPOSED_MODULES = {
    "myapp/books": "Books and their titles",
    "myapp/chapters": "Chapters of books",
    "myapp/reports": "Reports about books",
}

# A valid proposal for books.py: the module becomes the file of the action
# create_book (with the constant MAX_CHAPTERS), and Book moves to its own
# model file. _normalize_title is a helper function of create_book, so it
# moves with it.
BOOKS_CALLBACKS = [
    callback(
        "set_rename_to",
        module_name=BOOKS,
        location="@module",
        new_name="myapp/books/actions/create_book.py",
    ),
    callback(
        "set_code_unit_type",
        module_name=BOOKS,
        location="create_book",
        code_unit_type="action",
    ),
    callback(
        "set_code_unit_type",
        module_name=BOOKS,
        location="MAX_CHAPTERS",
        code_unit_type="constant",
    ),
    callback(
        "set_code_unit_type", module_name=BOOKS, location="Book", code_unit_type="model"
    ),
    callback(
        "set_move_to_file",
        module_name=BOOKS,
        location="Book",
        move_to_file="myapp/books/models/book.py",
    ),
]

# A valid proposal for create_chapter.py: the module becomes the file of the
# action create_chapter.
CHAPTERS_CALLBACKS = [
    callback(
        "set_rename_to",
        module_name=CREATE_CHAPTER,
        location="@module",
        new_name="myapp/chapters/actions/create_chapter.py",
    ),
    callback(
        "set_code_unit_type",
        module_name=CREATE_CHAPTER,
        location="create_chapter",
        code_unit_type="action",
    ),
]


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the propose-code-restructure stage. The target code (in
    the src dir) has the modules of the base env plus the modules that the
    test adds in myapp/reports. With the package grouping strategy, books.py
    is in group-1, the modules of myapp/chapters are in group-2, and the
    modules of myapp/reports are in group-3."""

    # Actions

    def create_session_at_propose_code_restructure(
        self, modules: T.Dict[str, str] = None
    ) -> None:
        """Creates a session for the target code with the added modules, whose
        next stage is propose-code-restructure. _normalize_title is a helper
        function of create_book, and the root package node file has the
        PROPOSED_MODULES."""
        self.create_session(
            modules,
            grouping_strategy="package",
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.edit_node_file(
            move_function_to_parent, BOOKS, "_normalize_title", "create_book"
        )
        for name, description in PROPOSED_MODULES.items():
            set_proposed_module(self.source_root, name, description)
        self.set_next_stage(STAGE)

    def script_base_modules(self) -> None:
        """Scripts the RFAs of books.py and of myapp/chapters with a valid
        proposal."""
        self.script_rfa(BOOKS_RFA_ID, *BOOKS_CALLBACKS)
        self.script_rfa(CHAPTERS_RFA_ID, *CHAPTERS_CALLBACKS)

    # Queries (for use in asserts)

    def callees_in_context(self, rfa_id: str, location: str) -> T.Set[T.Tuple]:
        """Returns the (callee, scope) pairs of the function view at the
        location, in the call graph view in the context of the RFA."""
        return {
            (call.location, call.scope)
            for call in self.function_view_in_context(rfa_id, location).callees
        }


def commit_messages(callbacks: T.List[Callback]) -> T.List[str]:
    """Returns the messages of the commits that Groupy makes after running
    the callbacks."""
    return [f"{STAGE}: {callback.name}" for callback in callbacks]
