from pathlib import Path

from groupy.sessions.rules.get_branch_dir import get_branch_dir


def get_request_dir(request_id: str) -> Path:
    # Holds the context of the Claude request, and the error of a failed callback
    return get_branch_dir() / "requests" / request_id
