import pytest

from apply_code_restructure_tests.apply_code_restructure_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch, capsys):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch, capsys=capsys)
