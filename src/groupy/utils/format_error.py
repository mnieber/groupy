def format_error(error: BaseException) -> str:
    # E.g. "DirtyWorkingTreeError: The working tree is not clean"
    name = type(error).__name__
    return f"{name}: {error}" if str(error) else name
