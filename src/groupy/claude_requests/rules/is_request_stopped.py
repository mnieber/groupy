from pathlib import Path


def is_request_stopped(request_dir: Path) -> bool:
    # A request stops when a callback fails twice in a row
    return (request_dir / "error.yaml").exists()
