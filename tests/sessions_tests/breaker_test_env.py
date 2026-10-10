import subprocess
import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest
from breaker.runtime.entrypoints.breaker import main as breaker_main
from breaker.sessions.models.session import Session, get_session, reset_session

BOOKS_PY = """\
MAX_CHAPTERS = 10


class Book:
    def __init__(self, title):
        self.title = title


def create_book(title):
    return Book(_normalize_title(title))


def _normalize_title(title):
    return title.strip()
"""

CREATE_CHAPTER_PY = """\
def create_chapter(book, title):
    return {"book": book, "title": title}
"""


@dataclass
class Context:
    """The pytest fixtures that breaker tests need. repo_dir is the (not yet
    existing) directory of the git repo that holds the target code."""

    repo_dir: Path
    monkeypatch: pytest.MonkeyPatch


class TestEnv:
    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.repo_dir = context.repo_dir
        self.session: Session = None
        self.remembered_git_head: str = None
        self.error: Exception = None
        # The session is a singleton, so a session of an earlier test must not
        # leak into this one.
        reset_session()
        self.__post_init__()

    def __post_init__(self):
        """Post-initialization hook for subclasses."""

    def step(self, *_: None) -> bool:
        return True

    # Actions

    def create_repo_with_target_code(self, target_dir: str = "src") -> None:
        """Creates a git repo (on branch `main`, with a clean working tree)
        with a README and the `myapp` package in target_dir. The cwd becomes
        the repo dir, which is where the developer runs breaker."""
        self.repo_dir.mkdir(parents=True)
        self.write_file("README.md", "# My app\n")
        self.write_file(f"{target_dir}/myapp/__init__.py", "")
        self.write_file(f"{target_dir}/myapp/books.py", BOOKS_PY)
        self.write_file(f"{target_dir}/myapp/chapters/__init__.py", "")
        self.write_file(
            f"{target_dir}/myapp/chapters/create_chapter.py", CREATE_CHAPTER_PY
        )
        self.run_git("init")
        self.run_git("config", "user.email", "test@example.com")
        self.run_git("config", "user.name", "Test")
        self.commit_all("initial commit")
        self.run_git("branch", "-M", "main")
        self.context.monkeypatch.chdir(self.repo_dir)

    def run_breaker(self, *args: str) -> None:
        breaker_main(list(args))

    def run_breaker_and_catch_error(self, *args: str) -> None:
        """Runs breaker and stores the exception it is expected to raise in
        env.error."""
        try:
            self.run_breaker(*args)
        except Exception as error:
            self.error = error

    def load_session(self) -> None:
        """Loads the session from the session file (not from the cached
        singleton) into env.session."""
        reset_session()
        self.session = get_session()

    def run_git(self, *args: str) -> None:
        self._git(*args)

    def commit_all(self, message: str) -> None:
        self.run_git("add", "-A")
        self.run_git("commit", "-m", message)

    def write_file(self, relative_path: str, text: str) -> None:
        path = self.repo_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def append_to_file(self, relative_path: str, text: str) -> None:
        path = self.repo_dir / relative_path
        path.write_text(path.read_text() + text)

    def remember_git_head(self) -> None:
        self.remembered_git_head = self.git_head()

    # Queries (for use in asserts)

    def file_exists(self, relative_path: str) -> bool:
        return (self.repo_dir / relative_path).exists()

    def node_file_paths(self) -> T.Set[str]:
        return {
            str(path.relative_to(self.repo_dir))
            for path in self.repo_dir.rglob("*.breaker.yaml")
        }

    def git_head(self) -> str:
        return self._git("rev-parse", "HEAD")

    def git_status(self) -> str:
        return self._git("status", "--porcelain")

    def git_branch(self) -> str:
        return self._git("rev-parse", "--abbrev-ref", "HEAD")

    def git_branches(self) -> T.Set[str]:
        return set(self._git("branch", "--format=%(refname:short)").splitlines())

    def files_in_head_commit(self) -> T.Set[str]:
        return set(self._git("show", "--name-only", "--format=", "HEAD").splitlines())

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
