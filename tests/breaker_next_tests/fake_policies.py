import typing as T
from dataclasses import dataclass
from pathlib import Path

from breaker.claude_requests.actions.run_callback import run_callback
from breaker.claude_requests.models.callback import Callback
from breaker.claude_requests.models.rfa import Rfa
from breaker.claude_requests.models.rfr import Rfr
from breaker.claude_requests.policies.rfa_policy import RfaPolicy
from breaker.claude_requests.policies.rfr_policy import RfrPolicy
from breaker.renamings.policies.rope_refactoring_policy import RopeRefactoringPolicy


class UnscriptedRequestError(Exception):
    pass


class FakeRefactoringError(Exception):
    pass


class FakeRfaPolicy(RfaPolicy):
    """Runs the scripted callbacks of each RFA, instead of asking Claude. It
    records the RFAs that it receives."""

    def __init__(self):
        self.scripts: T.Dict[str, T.List[Callback]] = {}
        self.requests: T.List[Rfa] = []

    def run(self, rfa: Rfa) -> None:
        self.requests.append(rfa)
        if rfa.id not in self.scripts:
            raise UnscriptedRequestError(f"There is no script for the RFA {rfa.id}")
        for callback in self.scripts[rfa.id]:
            run_callback(callback)


@dataclass
class FileWrite:
    """A step of an RFR script that writes the new text of a file, where the
    file path is relative to the repo dir (which is the cwd)."""

    file_path: str
    text: str


class FakeRfrPolicy(RfrPolicy):
    """Runs the scripted steps of each RFR (file writes and callbacks),
    instead of asking Claude to refactor the code. It records the RFRs that it
    receives."""

    def __init__(self):
        self.scripts: T.Dict[str, T.List[T.Union[FileWrite, Callback]]] = {}
        self.requests: T.List[Rfr] = []

    def run(self, rfr: Rfr) -> None:
        self.requests.append(rfr)
        if rfr.id not in self.scripts:
            raise UnscriptedRequestError(f"There is no script for the RFR {rfr.id}")
        for step in self.scripts[rfr.id]:
            if isinstance(step, FileWrite):
                Path(step.file_path).write_text(step.text)
            else:
                run_callback(step, in_rfr=True)


class FakeRefactoringPolicy(RopeRefactoringPolicy):
    """Refactors with rope, like the real policy, but raises an error for the
    refactorings that the test lets fail. It records the refactorings that it
    receives."""

    def __init__(self):
        super().__init__()
        # The (module_name, name) pairs of the refactorings that fail, where
        # name is the symbol that is renamed, moved or delegated, or @module
        # for move_module.
        self.failing_refactorings: T.Set[T.Tuple[str, str]] = set()
        # The (method, module_name, name) tuples of the refactorings, in the
        # order in which they were made.
        self.calls: T.List[T.Tuple[str, str, str]] = []

    def rename_symbol(
        self,
        source_root: Path,
        module_name: str,
        scope_location: str,
        name: str,
        new_name: str,
    ) -> None:
        self._record("rename_symbol", module_name, name)
        super().rename_symbol(source_root, module_name, scope_location, name, new_name)

    def move_module(
        self, source_root: Path, module_name: str, new_module_name: str
    ) -> None:
        self._record("move_module", module_name, "@module")
        super().move_module(source_root, module_name, new_module_name)

    def move_symbol(
        self, source_root: Path, module_name: str, name: str, target_module_name: str
    ) -> None:
        self._record("move_symbol", module_name, name)
        super().move_symbol(source_root, module_name, name, target_module_name)

    def delegate_method(
        self,
        source_root: Path,
        module_name: str,
        class_name: str,
        method_name: str,
        function_name: str,
    ) -> None:
        self._record("delegate_method", module_name, f"{class_name}.{method_name}")
        super().delegate_method(
            source_root, module_name, class_name, method_name, function_name
        )

    def _record(self, method: str, module_name: str, name: str) -> None:
        self.calls.append((method, module_name, name))
        if (module_name, name) in self.failing_refactorings:
            raise FakeRefactoringError(f"Cannot {method} {name} in {module_name}")


_fake_rfa_policy = FakeRfaPolicy()
_fake_rfr_policy = FakeRfrPolicy()
_fake_refactoring_policy = FakeRefactoringPolicy()


def get_fake_rfa_policy() -> FakeRfaPolicy:
    """The config of the tests refers to this function, so that Breaker uses
    the fake policy that the test has scripted."""
    return _fake_rfa_policy


def get_fake_rfr_policy() -> FakeRfrPolicy:
    """The config of the tests refers to this function, so that Breaker uses
    the fake policy that the test has scripted."""
    return _fake_rfr_policy


def get_fake_refactoring_policy() -> FakeRefactoringPolicy:
    """The config of the tests refers to this function, so that Breaker uses
    the fake policy that the test has scripted."""
    return _fake_refactoring_policy


def reset_fake_policies() -> None:
    global _fake_rfa_policy, _fake_rfr_policy, _fake_refactoring_policy
    _fake_rfa_policy = FakeRfaPolicy()
    _fake_rfr_policy = FakeRfrPolicy()
    _fake_refactoring_policy = FakeRefactoringPolicy()
