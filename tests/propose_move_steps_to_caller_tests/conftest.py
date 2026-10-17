import pytest

from propose_move_steps_to_caller_tests.propose_move_steps_to_caller_test_env import (
    Context,
)


@pytest.fixture
def context(tmp_path, monkeypatch):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch)
