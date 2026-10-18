from pathlib import PurePosixPath


def is_test_module(module_name: str) -> bool:
    path = PurePosixPath(module_name)
    return (
        "tests" in path.parts[:-1]
        or path.name.startswith("test_")
        or path.name.endswith("_test.py")
        or path.name == "conftest.py"
    )
