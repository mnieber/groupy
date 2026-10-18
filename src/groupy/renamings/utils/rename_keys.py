import typing as T


def rename_keys(
    entries: T.Dict[str, T.Any], renamings: T.Dict[str, str]
) -> T.Dict[str, T.Any]:
    # All keys are renamed at once (so text -> body and body -> content turn text
    # and body into body and content). A key that is not renamed keeps its own
    # value when another key is renamed to it.
    result: T.Dict[str, T.Any] = {}
    for key, value in entries.items():
        if key not in renamings:
            result[key] = value
    for key, value in entries.items():
        if key in renamings:
            result.setdefault(renamings[key], value)
    return {key: result[key] for key in _ordered_keys(entries, renamings, result)}


def _ordered_keys(
    entries: T.Dict[str, T.Any], renamings: T.Dict[str, str], result: T.Dict[str, T.Any]
) -> T.List[str]:
    # The keys keep the order of the original entries
    keys = []
    for key in entries:
        new_key = renamings.get(key, key)
        if new_key in result and new_key not in keys:
            keys.append(new_key)
    return keys
