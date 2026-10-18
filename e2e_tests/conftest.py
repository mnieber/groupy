import os
import shutil
import sys
from pathlib import Path

import pytest

# The e2e tests reuse the test envs of the normal tests
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from groupy_next_tests.groupy_next_test_env import Context  # noqa: E402


@pytest.fixture(autouse=True)
def require_e2e():
    # The e2e tests call Claude, which costs money, so they only run on request
    if os.environ.get("GROUPY_E2E") != "1":
        pytest.skip("The e2e tests call Claude: set GROUPY_E2E=1 to run them")
    if shutil.which("claude") is None:
        pytest.skip("The e2e tests need the claude executable on the PATH")


@pytest.fixture
def context(tmp_path, monkeypatch, capsys):
    return Context(repo_dir=tmp_path / "repo", monkeypatch=monkeypatch, capsys=capsys)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # A failed test points to the logs of the Claude sessions, to see what
    # Claude did
    outcome = yield
    report = outcome.get_result()
    context = item.funcargs.get("context") if hasattr(item, "funcargs") else None
    if report.failed and context is not None:
        logs_dir = context.repo_dir / ".groupy" / "logs"
        report.sections.append(("Claude logs", str(logs_dir)))
