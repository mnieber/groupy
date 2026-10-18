from abc import ABC, abstractmethod
from pathlib import Path


class RefactoringPolicy(ABC):
    @abstractmethod
    def rename_symbol(
        self,
        source_root: Path,
        module_name: str,
        scope_location: str,
        name: str,
        new_name: str,
    ) -> None:
        # Renames the symbol in the scope (@module, a class name or a function
        # location), including its imports and call sites in other modules
        pass

    @abstractmethod
    def move_module(
        self, source_root: Path, module_name: str, new_module_name: str
    ) -> None:
        pass

    @abstractmethod
    def move_symbol(
        self, source_root: Path, module_name: str, name: str, target_module_name: str
    ) -> None:
        pass

    @abstractmethod
    def delegate_method(
        self,
        source_root: Path,
        module_name: str,
        class_name: str,
        method_name: str,
        function_name: str,
    ) -> None:
        pass


class RenameConflictError(Exception):
    pass


class SymbolNotFoundError(Exception):
    pass
