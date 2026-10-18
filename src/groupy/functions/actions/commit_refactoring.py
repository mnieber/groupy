import ast
from pathlib import Path

from groupy.sessions.actions.commit_stage_changes import commit_stage_changes
from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.rules.get_changed_files import get_changed_files


def commit_refactoring(description: str) -> None:
    # Commits the source and the node files together, if the changed Python files
    # parse
    for file_path in get_changed_files():
        path = Path(file_path)
        if path.suffix != ".py" or not path.exists():
            continue
        try:
            ast.parse(path.read_text())
        except SyntaxError as error:
            restore_working_tree()
            raise RefactoringDoesNotParseError(
                f"The refactoring broke the syntax of {file_path}: {error}"
            )
    commit_stage_changes(description)


class RefactoringDoesNotParseError(Exception):
    pass
