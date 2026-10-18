import typing as T

from groupy.nodes.utils.exceptions import EntryNotFoundError


def check_has_entry(entries: T.Union[T.Dict, T.List], entry: str, field: str) -> None:
    if entry not in entries:
        raise EntryNotFoundError(f"The {field} have no entry {entry}")
