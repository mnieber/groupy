import typing as T

from dataclassy import values
from dataclassy.functions import is_dataclass_instance


def dataclass_to_dict(obj: T.Any) -> T.Dict[str, T.Any]:
    # Fields that have their default value are left out
    defaults = type(obj).__defaults__
    result = {}
    for name, value in values(obj).items():
        if name in defaults and value == defaults[name]:
            continue
        result[name] = _to_plain_value(value)
    return result


def _to_plain_value(value: T.Any) -> T.Any:
    if isinstance(value, list):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain_value(item) for key, item in value.items()}
    if is_dataclass_instance(value):
        return dataclass_to_dict(value)
    return value
