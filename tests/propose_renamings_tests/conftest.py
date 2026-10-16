import pytest

from propose_renamings_tests.propose_renamings_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch)
