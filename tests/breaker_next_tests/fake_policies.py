import typing as T
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


class FakeRfrPolicy(RfrPolicy):
    """Writes the scripted files of each RFR, instead of asking Claude to
    refactor the code. It records the RFRs that it receives."""

    def __init__(self):
        # Maps each RFR id onto the new texts of the files that it changes,
        # by file path (relative to the repo dir, which is the cwd).
        self.scripts: T.Dict[str, T.Dict[str, str]] = {}
        self.requests: T.List[Rfr] = []

    def run(self, rfr: Rfr) -> None:
        self.requests.append(rfr)
        if rfr.id not in self.scripts:
            raise UnscriptedRequestError(f"There is no script for the RFR {rfr.id}")
        for file_path, text in self.scripts[rfr.id].items():
            Path(file_path).write_text(text)


class FakeRefactoringPolicy(RopeRefactoringPolicy):
    """Refactors with rope, like the real policy, but raises an error for the
    renames that the test lets fail. It records the renames that it
    receives."""

    def __init__(self):
        super().__init__()
        # The (module_name, name) pairs of the renames that fail.
        self.failing_renames: T.Set[T.Tuple[str, str]] = set()
        # The (module_name, scope_location, name, new_name) tuples of the
        # renames, in the order in which they were made.
        self.renames: T.List[T.Tuple[str, str, str, str]] = []

    def rename_symbol(
        self,
        source_root: Path,
        module_name: str,
        scope_location: str,
        name: str,
        new_name: str,
    ) -> None:
        self.renames.append((module_name, scope_location, name, new_name))
        if (module_name, name) in self.failing_renames:
            raise FakeRefactoringError(f"Cannot rename {name} in {module_name}")
        super().rename_symbol(source_root, module_name, scope_location, name, new_name)


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
