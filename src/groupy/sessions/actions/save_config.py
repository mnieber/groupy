from pathlib import Path

from dataclassy import values
from groupy.sessions.models.config import Config
from groupy.utils.dump_yaml import dump_yaml


def save_config(config: Config, config_path: Path) -> None:
    # Every field is written, so that the developer can see what can be configured
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(dump_yaml(values(config)))
