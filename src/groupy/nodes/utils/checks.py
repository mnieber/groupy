import typing as T

from dataclassy import fields

from groupy.nodes.utils.exceptions import (
    EntryNotFoundError,
    FieldNotSupportedError,
    InvalidIndexError,
)


def check_has_entry(entries: T.Union[T.Dict, T.List], entry: str, field: str) -> None:
    if entry not in entries:
        raise EntryNotFoundError(f"The {field} have no entry {entry}")


def check_index(items: T.List[T.Any], index: int, allow_end: bool = False) -> None:
    # With allow_end, the index may point just after the last item
    max_index = len(items) if allow_end else len(items) - 1
    if not 0 <= index <= max_index:
        raise InvalidIndexError(f"The index {index} is not in the range 0..{max_index}")


def check_has_field(obj: T.Any, field: str) -> None:
    if field not in fields(obj):
        name = getattr(obj, "name", None)
        description = f"{type(obj).__name__} ({name})" if name else type(obj).__name__
        raise FieldNotSupportedError(f"A {description} has no field {field}")
