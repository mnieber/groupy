import typing as T

from dataclassy import fields
from groupy.nodes.utils.exceptions import FieldNotSupportedError


def check_node_has_field(node: T.Any, field: str) -> None:
    if field not in fields(node):
        raise FieldNotSupportedError(
            f"A {type(node).__name__} ({node.name}) has no field {field}"
        )
