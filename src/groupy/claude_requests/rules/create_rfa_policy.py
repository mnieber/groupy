from groupy.claude_requests.policies.rfa_policy import RfaPolicy
from groupy.sessions.models.config import Config
from groupy.utils.import_object import import_object


def create_rfa_policy(config: Config) -> RfaPolicy:
    # The config names a callable that returns the policy
    return import_object(config.rfa_policy)()
