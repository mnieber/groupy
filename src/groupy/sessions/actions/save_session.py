from groupy.sessions.models.session import Session
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.utils.dataclass_to_dict import dataclass_to_dict
from groupy.utils.dump_yaml import dump_yaml


def save_session(session: Session) -> None:
    session_path = get_groupy_path("session.yaml")
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(dump_yaml(dataclass_to_dict(session)))
