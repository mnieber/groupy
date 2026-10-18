import typing as T


def order_renamings(renamings: T.List[T.Tuple[str, str]]) -> T.List[T.Tuple[str, str]]:
    # Orders the renamings so that a chain works: for title -> text and
    # text -> body, text is renamed first. The renamings have no cycles.
    pending = list(renamings)
    result = []
    while pending:
        old_names = {old for old, _ in pending}
        ready = [renaming for renaming in pending if renaming[1] not in old_names]
        if not ready:
            raise ValueError(f"The renamings form a cycle: {pending}")
        result.append(ready[0])
        pending.remove(ready[0])
    return result
