class NoSessionError(Exception):
    pass


class NoGroupFileError(Exception):
    pass


class DirtyWorkingTreeError(Exception):
    pass


class NoGroupyBranchError(Exception):
    pass


class StageNotStartedError(Exception):
    pass


class DetachedHeadError(Exception):
    pass


class BranchDirsNotIgnoredError(Exception):
    pass
