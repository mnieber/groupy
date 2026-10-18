from pathlib import Path

import yaml

from groupy.sessions.models.config import Config


def load_config(config_path: Path) -> Config:
    # Fields that are missing in the config file get their default value
    data = yaml.safe_load(config_path.read_text()) if config_path.exists() else None
    return Config(**(data or {}))
