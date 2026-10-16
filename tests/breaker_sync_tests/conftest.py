import pytest

from breaker_sync_tests.breaker_sync_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch, capsys):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch, capsys=capsys)
