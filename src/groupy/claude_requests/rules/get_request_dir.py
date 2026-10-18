from pathlib import Path

from groupy.sessions.rules.get_groupy_path import get_groupy_path


def get_request_dir(request_id: str) -> Path:
    # Holds the context of the Claude request, and the error of a failed callback
    return get_groupy_path("requests") / request_id
