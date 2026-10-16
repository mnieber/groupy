import typing as T

from breaker.claude_requests.actions.run_callback import run_callback
from breaker.claude_requests.models.callback import Callback
from breaker.claude_requests.models.rfa import Rfa
from breaker.claude_requests.policies.rfa_policy import RfaPolicy


class UnscriptedRequestError(Exception):
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


_fake_rfa_policy = FakeRfaPolicy()


def get_fake_rfa_policy() -> FakeRfaPolicy:
    """The config of the tests refers to this function, so that Breaker uses
    the fake policy that the test has scripted."""
    return _fake_rfa_policy


def reset_fake_policies() -> None:
    global _fake_rfa_policy
    _fake_rfa_policy = FakeRfaPolicy()
