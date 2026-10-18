from pathlib import Path

from groupy.utils.dump_yaml import dump_yaml


def save_callback_error(request_dir: Path, error: BaseException) -> None:
    # The policy that waits for Claude raises this error again
    error_class = type(error)
    data = {
        "error_class": f"{error_class.__module__}:{error_class.__qualname__}",
        "message": str(error),
    }
    (request_dir / "error.yaml").write_text(dump_yaml(data))
