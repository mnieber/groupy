from groupy.sessions.models.last_run import LastRun
from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.utils.dataclass_to_dict import dataclass_to_dict
from groupy.utils.dump_yaml import dump_yaml


def save_last_run(last_run: LastRun) -> None:
    path = get_branch_dir() / "last-run.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(dataclass_to_dict(last_run)))
