from groupy.claude_requests.actions.run_claude import run_claude
from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.policies.rfa_policy import RfaPolicy
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.load_config import load_config


class ClaudeRfaPolicy(RfaPolicy):
    def __init__(self):
        self.config = load_config(get_groupy_path("config.yaml"))

    def run(self, rfa: Rfa) -> None:
        run_claude(
            rfa.id, rfa.prompt, rfa.context, self.config.claude_model, in_rfr=False
        )
