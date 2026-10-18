from groupy.sessions.models.config import Config
from groupy.sessions.models.session import get_session


def get_claude_model(config: Config) -> str:
    # A stage may have a model of its own (e.g. a stronger model for a stage that
    # needs more judgement). An empty model is the default model of Claude Code.
    return config.claude_model_by_stage.get(
        get_session().next_stage, config.claude_model
    )
