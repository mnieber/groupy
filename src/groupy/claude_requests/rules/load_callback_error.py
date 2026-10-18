import typing as T
from pathlib import Path

import yaml

from groupy.claude_requests.utils.exceptions import CallbackFailedError
from groupy.utils.import_object import import_object


def load_callback_error(request_dir: Path) -> T.Optional[BaseException]:
    # Recreates the error of the failed callback of the request, if any
    error_path = request_dir / "error.yaml"
    if not error_path.exists():
        return None
    data = yaml.safe_load(error_path.read_text())
    try:
        return import_object(data["error_class"])(data["message"])
    except Exception:
        return CallbackFailedError(f"{data['error_class']}: {data['message']}")
