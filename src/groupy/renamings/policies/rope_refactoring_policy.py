import ast
from pathlib import Path, PurePosixPath

from rope.base.project import Project
from rope.refactor.move import MoveModule, create_move
from rope.refactor.rename import Rename

from groupy.renamings.actions.create_packages import create_packages
from groupy.renamings.policies.refactoring_policy import (
    RefactoringPolicy,
    RenameConflictError,
    SymbolNotFoundError,
)
from groupy.renamings.rules.create_delegation import create_delegation
from groupy.renamings.rules.find_scope_def import find_scope_def
from groupy.renamings.rules.get_scope_symbols import get_scope_symbols
from groupy.renamings.utils.get_symbol_offset import get_symbol_offset


class RopeRefactoringPolicy(RefactoringPolicy):
    def rename_symbol(
        self,
        source_root: Path,
        module_name: str,
        scope_location: str,
        name: str,
        new_name: str,
    ) -> None:
        text = (source_root / module_name).read_text()
        scope_def = find_scope_def(ast.parse(text), scope_location)
        symbols = get_scope_symbols(scope_def) if scope_def else {}
        if name not in symbols:
            raise SymbolNotFoundError(
                f"{module_name}:{scope_location} has no symbol {name}"
            )

        # Check for a clash before any file is changed
        if new_name in symbols:
            raise RenameConflictError(
                f"Cannot rename {name} to {new_name} in {module_name}:{scope_location}, "
                f"because {new_name} already exists"
            )

        offset = get_symbol_offset(text, symbols[name], name)
        project = _open_project(source_root)
        try:
            resource = project.get_resource(module_name)
            changes = Rename(project, resource, offset).get_changes(new_name)
            project.do(changes)
        finally:
            project.close()

    def move_module(
        self, source_root: Path, module_name: str, new_module_name: str
    ) -> None:
        old_path = PurePosixPath(module_name)
        new_path = PurePosixPath(new_module_name)
        project = _open_project(source_root)
        try:
            # First rename the module in its dir (via a temporary name if the new
            # name is taken), so that a new package with the old name of the
            # module (e.g. myapp/books for myapp/books.py) does not clash with it
            current_path = old_path
            if old_path.name != new_path.name:
                current_path = old_path.with_name(new_path.name)
                if (source_root / current_path).exists():
                    current_path = old_path.with_name(f"_groupy_{new_path.name}")
                resource = project.get_resource(str(old_path))
                project.do(Rename(project, resource).get_changes(current_path.stem))

            # Then move it to its new package
            if current_path.parent != new_path.parent:
                create_packages(source_root, new_module_name)
                project.validate()
                resource = project.get_resource(str(current_path))
                destination = project.get_resource(str(new_path.parent))
                project.do(MoveModule(project, resource).get_changes(destination))
                current_path = new_path.parent / current_path.name
            if current_path.name != new_path.name:
                resource = project.get_resource(str(current_path))
                project.do(Rename(project, resource).get_changes(new_path.stem))
        finally:
            project.close()

    def move_symbol(
        self, source_root: Path, module_name: str, name: str, target_module_name: str
    ) -> None:
        text = (source_root / module_name).read_text()
        symbols = get_scope_symbols(ast.parse(text))
        if name not in symbols:
            raise SymbolNotFoundError(f"{module_name} has no symbol {name}")

        # The target module is created when it does not exist yet
        target_path = source_root / target_module_name
        if not target_path.exists():
            create_packages(source_root, target_module_name)
            target_path.write_text("")
        project = _open_project(source_root)
        try:
            resource = project.get_resource(module_name)
            offset = get_symbol_offset(text, symbols[name], name)
            mover = create_move(project, resource, offset)
            destination = project.get_resource(target_module_name)
            project.do(mover.get_changes(destination))
        finally:
            project.close()

    def delegate_method(
        self,
        source_root: Path,
        module_name: str,
        class_name: str,
        method_name: str,
        function_name: str,
    ) -> None:
        path = source_root / module_name
        path.write_text(
            create_delegation(path.read_text(), class_name, method_name, function_name)
        )


def _open_project(source_root: Path) -> Project:
    # Without a rope folder, rope does not add files to the repository. New imports
    # have the form `from <module> import <name>`.
    project = Project(str(source_root), ropefolder=None)
    project.prefs.imports.preferred_import_style = "from-global"
    return project
