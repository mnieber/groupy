from groupy.claude_requests.actions.run_claude import run_claude
from groupy.claude_requests.models.rfr import Rfr
from groupy.claude_requests.policies.rfr_policy import RfrPolicy
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.load_config import load_config


class ClaudeRfrPolicy(RfrPolicy):
    def __init__(self):
        self.config = load_config(get_groupy_path("config.yaml"))

    def run(self, rfr: Rfr) -> None:
        run_claude(
            rfr.id, rfr.prompt, rfr.context, self.config.claude_model, in_rfr=True
        )
