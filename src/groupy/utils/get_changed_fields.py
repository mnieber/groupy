import typing as T

from dataclassy import values


def get_changed_fields(node: T.Any) -> T.List[str]:
    # The fields (other than name) that do not have their default value
    defaults = type(node).__defaults__
    return [
        field
        for field, value in values(node).items()
        if field in defaults and value != defaults[field]
    ]
