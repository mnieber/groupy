from abc import ABC, abstractmethod

from groupy.claude_requests.models.rfa import Rfa


class RfaPolicy(ABC):
    # Sends the RFA to Claude, and runs the callbacks of Claude (with run_callback)
    @abstractmethod
    def run(self, rfa: Rfa) -> None:
        pass
