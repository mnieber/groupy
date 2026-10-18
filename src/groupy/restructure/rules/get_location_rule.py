import typing as T
from pathlib import PurePosixPath

from groupy.utils.to_snake_case import to_snake_case


def get_location_rule(
    code_unit_type: str, name: str
) -> T.Optional[T.Tuple[T.Callable[[PurePosixPath], bool], str]]:
    # Returns a check of the target file of a code unit, and a description of the
    # location that the check expects (None when the code unit may go anywhere)
    file_name = f"{to_snake_case(name)}.py"
    if code_unit_type in ("action", "rule", "util", "model", "policy"):
        dir_name = f"{code_unit_type}s" if code_unit_type != "policy" else "policies"
        return (
            lambda path: path.parent.name == dir_name,
            f"<package>/{dir_name}/{file_name}",
        )
    if code_unit_type == "entrypoint":
        return (
            lambda path: path.parent.parts[-2:] == ("runtime", "entrypoints"),
            f"<app_package>/runtime/entrypoints/{file_name}",
        )
    if code_unit_type == "enum":
        return (lambda path: path.name == "enums.py", "<package>/enums.py")
    if code_unit_type == "setting":
        return (lambda path: path.name == "settings.py", "<app_package>/settings.py")
    return None
