import typing as T

from groupy.nodes.utils.exceptions import InvalidIndexError


def check_index(items: T.List[T.Any], index: int, allow_end: bool = False) -> None:
    # With allow_end, the index may point just after the last item
    max_index = len(items) if allow_end else len(items) - 1
    if not 0 <= index <= max_index:
        raise InvalidIndexError(f"The index {index} is not in the range 0..{max_index}")
