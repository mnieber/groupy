from abc import ABC, abstractmethod

from groupy.claude_requests.models.rfr import Rfr


class RfrPolicy(ABC):
    # Sends the RFR to Claude, who edits the source and runs callbacks (with
    # run_callback in RFR mode)
    @abstractmethod
    def run(self, rfr: Rfr) -> None:
        pass
