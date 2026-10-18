import importlib
import typing as T


def import_object(import_path: str) -> T.Any:
    # The import path has the form <module>:<name>
    module_name, name = import_path.split(":", 1)
    return getattr(importlib.import_module(module_name), name)
