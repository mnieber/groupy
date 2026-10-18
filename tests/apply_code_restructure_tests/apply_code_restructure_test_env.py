import ast
import textwrap
import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

from groupy.functions.actions.move_function_to_parent import move_function_to_parent
from groupy.nodes.actions.set_code_unit_type import set_code_unit_type
from groupy.nodes.actions.set_move_to_file import set_move_to_file
from groupy.nodes.actions.set_rename_to import set_rename_to
from groupy.package_nodes.models.package_node import PackageNode
from groupy.package_nodes.rules.load_package_node import load_package_node

__all__ = ["Context", "TestEnv"]

STAGE = "apply-code-restructure"

BOOKS = "myapp/books.py"
CREATE_CHAPTER = "myapp/chapters/create_chapter.py"

CREATE_BOOK = "myapp/books/actions/create_book.py"
BOOK = "myapp/books/models/book.py"
NEW_CREATE_CHAPTER = "myapp/chapters/actions/create_chapter.py"


class TestEnv(GroupyNextTestEnv):
    """A TestEnv for the apply-code-restructure stage. The target code (in the
    src dir) has the modules of the base env plus the modules that the test
    adds in myapp/reports. With the package grouping strategy, books.py is in
    group-1, the modules of myapp/chapters are in group-2, and the modules of
    myapp/reports are in group-3."""

    def __init__(self, context: Context):
        self.package_node: PackageNode = None
        super().__init__(context)

    # Actions

    def create_session_at_apply_code_restructure(
        self, modules: T.Dict[str, str] = None
    ) -> None:
        """Creates a session for the target code with the added modules, whose
        next stage is apply-code-restructure, with a valid proposal for the
        modules of the base env:
        - books.py is renamed to the file of the action create_book (with its
          helper function _normalize_title and the constant MAX_CHAPTERS), and
          the model Book moves to its own file;
        - create_chapter.py is renamed to the file of the action
          create_chapter.
        The test adds (and commits) the proposal for its own modules."""
        self.create_session(
            modules,
            grouping_strategy="package",
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.edit_node_file(
            move_function_to_parent, BOOKS, "_normalize_title", "create_book"
        )
        self.edit_node_file(set_rename_to, BOOKS, "@module", CREATE_BOOK)
        self.edit_node_file(set_code_unit_type, BOOKS, "create_book", "action")
        self.edit_node_file(set_code_unit_type, BOOKS, "MAX_CHAPTERS", "constant")
        self.edit_node_file(set_code_unit_type, BOOKS, "Book", "model")
        self.edit_node_file(set_move_to_file, BOOKS, "Book", BOOK)
        self.edit_node_file(
            set_rename_to, CREATE_CHAPTER, "@module", NEW_CREATE_CHAPTER
        )
        self.edit_node_file(
            set_code_unit_type, CREATE_CHAPTER, "create_chapter", "action"
        )
        self.set_next_stage(STAGE)

    def load_package_node(self, package_name: str) -> None:
        self.package_node = load_package_node(
            self.source_root / package_name / "package-node.groupy.yaml"
        )

    # Queries (for use in asserts)

    def module_exists(self, module_name: str) -> bool:
        return (self.source_root / module_name).exists()

    def top_level_names(self, module_name: str) -> T.List[str]:
        """Returns the names of the top-level functions, classes and variables
        of the module, in source order."""
        names = []
        for statement in self._parse(module_name).body:
            if isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                names.append(statement.name)
            elif isinstance(statement, ast.Assign):
                names.extend(
                    target.id
                    for target in statement.targets
                    if isinstance(target, ast.Name)
                )
        return names

    def imported_names(self, module_name: str) -> T.Dict[str, T.List[str]]:
        """Returns the names that the module imports at the module level, by
        the module that they are imported from (e.g.
        {"myapp.books.models.book": ["Book"]})."""
        imported_names = {}
        for statement in self._parse(module_name).body:
            if isinstance(statement, ast.ImportFrom):
                imported_names.setdefault(statement.module, []).extend(
                    alias.name for alias in statement.names
                )
        return imported_names

    def function_source(self, module_name: str, location: str) -> str:
        """Returns the (dedented) source of the function or method at the
        location (e.g. `create_book` or `Report.render`) in the module."""
        text = (self.source_root / module_name).read_text()
        statements = self._parse(module_name).body
        node = None
        for name in location.split("."):
            matches = [
                statement
                for statement in statements
                if isinstance(statement, (ast.FunctionDef, ast.ClassDef))
                and statement.name == name
            ]
            assert len(matches) == 1, f"Expected one definition of {location}"
            node = matches[0]
            statements = node.body
        segment = ast.get_source_segment(text, node, padded=True)
        return textwrap.dedent(segment)

    def python_files_that_do_not_parse(self) -> T.List[str]:
        result = []
        for path in sorted(self.source_root.rglob("*.py")):
            try:
                ast.parse(path.read_text())
            except SyntaxError:
                result.append(str(path.relative_to(self.source_root)))
        return result

    def group_of(self, module_name: str) -> int:
        """Returns the (1-based) number of the group of the module in
        env.groups."""
        matches = [
            nr
            for nr, group in enumerate(self.groups, start=1)
            if module_name in group.module_names
        ]
        assert len(matches) == 1, f"Expected {module_name} in one group"
        return matches[0]

    def _parse(self, module_name: str) -> ast.Module:
        return ast.parse((self.source_root / module_name).read_text())
