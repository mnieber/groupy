import pytest

from sessions_tests.breaker_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch)
