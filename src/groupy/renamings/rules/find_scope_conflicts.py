import typing as T


def find_scope_conflicts(
    renamings: T.List[T.Tuple[str, str]], existing_names: T.Set[str]
) -> T.List[str]:
    # Returns a description per conflict between the (old name, new name) pairs of
    # one scope. A chain (e.g. title -> text and text -> body) is allowed, since the
    # renames can be ordered so that they work.
    conflicts = []
    old_names = {old for old, _ in renamings}

    for old, new in renamings:
        if new in existing_names and new not in old_names:
            conflicts.append(f"{old} -> {new} clashes with the existing name {new}")

    old_names_by_new_name: T.Dict[str, T.List[str]] = {}
    for old, new in renamings:
        old_names_by_new_name.setdefault(new, []).append(old)
    for new, olds in old_names_by_new_name.items():
        if len(olds) > 1:
            parts = [f"{old} -> {new}" for old in sorted(olds)]
            conflicts.append(f"{' and '.join(parts)} have the same new name")

    # A cycle cannot be applied without a temporary name
    new_name_by_old_name = dict(renamings)
    reported: T.Set[str] = set()
    for start in sorted(new_name_by_old_name):
        cycle = _find_cycle(new_name_by_old_name, start)
        if cycle and not reported.intersection(cycle):
            reported.update(cycle)
            parts = [f"{old} -> {new_name_by_old_name[old]}" for old in sorted(cycle)]
            conflicts.append(f"{' and '.join(parts)} form a cycle")
    return conflicts


def _find_cycle(
    new_name_by_old_name: T.Dict[str, str], start: str
) -> T.Optional[T.List[str]]:
    path = [start]
    name = new_name_by_old_name[start]
    while name in new_name_by_old_name:
        if name == start:
            return path
        if name in path:
            return None
        path.append(name)
        name = new_name_by_old_name[name]
    return None
