import pytest
from identify_helper_functions_tests.identify_helper_functions_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch)
