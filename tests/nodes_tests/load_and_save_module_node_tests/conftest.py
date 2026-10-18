import pytest
from load_and_save_module_node_tests.node_file_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch):
    return Context(source_root=tmp_path / "src", monkeypatch=monkeypatch)
