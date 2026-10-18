from groupy.renamings.policies.refactoring_policy import RefactoringPolicy
from groupy.sessions.models.config import Config
from groupy.utils.import_object import import_object


def create_refactoring_policy(config: Config) -> RefactoringPolicy:
    # The config names a callable that returns the policy
    return import_object(config.refactoring_policy)()
