import pytest

from glossary_tests.glossary_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch):
    return Context(source_root=tmp_path / "src", monkeypatch=monkeypatch)
