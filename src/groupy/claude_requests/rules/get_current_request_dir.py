import typing as T
from pathlib import Path

from groupy import settings


def get_current_request_dir() -> T.Optional[Path]:
    # The dir of the Claude request that runs the callback (none when the
    # developer runs a callback by hand)
    if not settings.GROUPY_REQUEST_DIR:
        return None
    return Path(settings.GROUPY_REQUEST_DIR)
