import pytest

from call_graph_tests.call_graph_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch):
    return Context(repo_dir=tmp_path, monkeypatch=monkeypatch)
