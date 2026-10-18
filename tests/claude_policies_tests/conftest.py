import pytest
from claude_policies_tests.claude_policies_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch, capsys):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch, capsys=capsys)
