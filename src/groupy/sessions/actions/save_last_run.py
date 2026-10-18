from groupy.sessions.models.last_run import LastRun
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.utils.dataclass_to_dict import dataclass_to_dict
from groupy.utils.dump_yaml import dump_yaml


def save_last_run(last_run: LastRun) -> None:
    get_groupy_path("last-run.yaml").write_text(dump_yaml(dataclass_to_dict(last_run)))
