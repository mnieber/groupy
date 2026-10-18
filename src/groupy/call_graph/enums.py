from enum import Enum


class CallScopes(str, Enum):
    SAME_MODULE = "same-module"
    CHUNK = "chunk"
    OUTSIDE_CHUNK = "outside-chunk"
