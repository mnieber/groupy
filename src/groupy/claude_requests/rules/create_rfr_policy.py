from groupy.claude_requests.policies.rfr_policy import RfrPolicy
from groupy.sessions.models.config import Config
from groupy.utils.import_object import import_object


def create_rfr_policy(config: Config) -> RfrPolicy:
    # The config names a callable that returns the policy
    return import_object(config.rfr_policy)()
