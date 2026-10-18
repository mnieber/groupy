import typing as T
from enum import Enum
from pathlib import Path

from dataclassy import values
from dataclassy.functions import is_dataclass_instance


def to_plain_data(value: T.Any) -> T.Any:
    # Converts models, enums and paths (also nested ones) to data that can be
    # written as yaml
    if is_dataclass_instance(value):
        return {name: to_plain_data(item) for name, item in values(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_plain_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_plain_data(item) for item in value]
    return value
