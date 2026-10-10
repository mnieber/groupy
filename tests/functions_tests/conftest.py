import pytest

from functions_tests.functions_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch):
    return Context(source_root=tmp_path / "src", monkeypatch=monkeypatch)
