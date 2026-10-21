class NodeNotFoundError(Exception):
    pass


class EmbeddedFunctionNodeNotFoundError(NodeNotFoundError):
    pass


class AmbiguousLocationError(Exception):
    pass


class EntryNotFoundError(Exception):
    pass


class FieldNotSupportedError(Exception):
    pass


class InvalidValueError(Exception):
    pass


class InvalidIndexError(Exception):
    pass
