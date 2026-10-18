import typing as T

from groupy import settings
from groupy.claude_requests.actions.run_callback import run_callback
from groupy.claude_requests.actions.save_callback_error import save_callback_error
from groupy.claude_requests.models.callback import Callback
from groupy.claude_requests.rules.get_current_request_dir import (
    get_current_request_dir,
)
from groupy.claude_requests.rules.is_request_stopped import is_request_stopped
from groupy.utils.dump_yaml import dump_yaml
from groupy.utils.format_error import format_error


def run_requested_callback(callback: Callback) -> T.Any:
    # Runs a callback that Claude requested. A failed callback may be retried
    # once: when the next callback fails too, the request ends, and later
    # callbacks of the request are refused.
    request_dir = get_current_request_dir()
    if request_dir is None:
        return run_callback(callback, in_rfr=settings.GROUPY_IN_RFR)
    if is_request_stopped(request_dir):
        raise RequestStoppedError("An earlier callback of this request failed")

    failed_callback_path = request_dir / "failed-callback.yaml"
    try:
        result = run_callback(callback, in_rfr=settings.GROUPY_IN_RFR)
    except Exception as error:
        if failed_callback_path.exists():
            save_callback_error(request_dir, error)
        else:
            failed_callback_path.write_text(
                dump_yaml({"callback": callback.name, "error": format_error(error)})
            )
        raise
    failed_callback_path.unlink(missing_ok=True)
    return result


class RequestStoppedError(Exception):
    pass
