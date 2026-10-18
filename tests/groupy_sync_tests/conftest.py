import pytest
from groupy_sync_tests.groupy_sync_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch, capsys):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch, capsys=capsys)
