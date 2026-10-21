import subprocess
import typing as T
from dataclasses import dataclass
from pathlib import Path

import pytest

from groupy.groups.models.group import Group
from groupy.groups.rules.load_group_file import load_group_file
from groupy.runtime.entrypoints.groupy import run as groupy_run
from groupy.sessions.models.config import Config
from groupy.sessions.models.session import Session, get_session, reset_session
from groupy.sessions.rules.load_config import load_config

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
    """The pytest fixtures that groupy tests need. repo_dir is the (not yet
    existing) directory of the git repo that holds the target code. capsys
    captures what Groupy prints (it is only needed by tests that look at the
    output)."""

    repo_dir: Path
    monkeypatch: pytest.MonkeyPatch
    capsys: pytest.CaptureFixture = None


class TestEnv:
    # Stops pytest from trying to collect this base class as a test class.
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.repo_dir = context.repo_dir
        self.session: Session = None
        self.config: Config = None
        self.groups: T.List[Group] = []
        self.remembered_git_head: str = None
        self.error: Exception = None
        self.output: str = ""
        self.exit_code: int = None
        self.system_exit: SystemExit = None
        self.prompts: T.List[str] = []
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
        with a README, a .gitignore for the
        per-branch dirs of Groupy, and the `myapp` package in target_dir. The
        cwd becomes the repo dir, which is where the developer runs groupy."""
        self.repo_dir.mkdir(parents=True)
        self.write_file("README.md", "# My app\n")
        self.write_file(".gitignore", "/.groupy/*/\n")
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

    def run_groupy(self, *args: str) -> None:
        # Each groupy command runs in a new process, which loads the session
        # file anew
        reset_session()
        groupy_run(list(args))

    def run_groupy_and_catch_error(self, *args: str) -> None:
        """Runs groupy and stores the exception it is expected to raise in
        env.error."""
        try:
            self.run_groupy(*args)
        except Exception as error:
            self.error = error

    def run_groupy_cli(self, *args: str) -> None:
        """Runs groupy like the console script does, which prints errors
        instead of raising them. Stores the exit code in env.exit_code, and what
        groupy printed (to stdout and stderr) in env.output."""
        # Imported here, so that the tests that don't need it run without it
        from groupy.runtime.entrypoints.groupy import main as groupy_main

        reset_session()
        self.context.capsys.readouterr()
        self.exit_code = groupy_main(list(args))
        captured = self.context.capsys.readouterr()
        self.output = captured.out + captured.err

    def run_groupy_and_catch_exit(self, *args: str) -> None:
        """Runs groupy like the console script does, and stores the SystemExit
        that it is expected to raise (e.g. for invalid arguments) in
        env.system_exit, and what groupy printed in env.output."""
        # Imported here, so that the tests that don't need it run without it
        from groupy.runtime.entrypoints.groupy import main as groupy_main

        reset_session()
        self.context.capsys.readouterr()
        try:
            groupy_main(list(args))
        except SystemExit as system_exit:
            self.system_exit = system_exit
        captured = self.context.capsys.readouterr()
        self.output = captured.out + captured.err

    def answer_prompts(self, answer: T.Optional[str]) -> None:
        """Lets the developer give the answer when groupy asks a question, and
        stores the questions in env.prompts. Without an answer, a question
        fails the test."""

        def _input(prompt: str = "") -> str:
            self.prompts.append(prompt)
            assert answer is not None, f"Groupy asked: {prompt}"
            return answer

        self.context.monkeypatch.setattr("builtins.input", _input)

    def load_session(self) -> None:
        """Loads the session from the session file (not from the cached
        singleton) into env.session."""
        reset_session()
        self.session = get_session()

    def load_config(self) -> None:
        self.config = load_config(self.repo_dir / ".groupy" / "config.yaml")

    def load_groups(self) -> None:
        self.groups = load_group_file(self.repo_dir / ".groupy" / "groups.txt")

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

    def read_file(self, relative_path: str) -> str:
        return (self.repo_dir / relative_path).read_text()

    def file_exists(self, relative_path: str) -> bool:
        return (self.repo_dir / relative_path).exists()

    def node_file_paths(self) -> T.Set[str]:
        return {
            str(path.relative_to(self.repo_dir))
            for path in self.repo_dir.rglob("*.groupy.yaml")
        }

    def module_names_per_group(self) -> T.List[T.List[str]]:
        return [group.module_names for group in self.groups]

    def output_contains(self, *fragments: str) -> bool:
        """Returns whether every fragment occurs in env.output. A failing
        assert prints the output, to show what is missing."""
        missing = [fragment for fragment in fragments if fragment not in self.output]
        assert not missing, f"Missing {missing} in the output:\n{self.output}"
        return True

    def git_head(self) -> str:
        return self._git("rev-parse", "HEAD")

    def git_status(self) -> str:
        return self._git("status", "--porcelain")

    def git_branch(self) -> str:
        return self._git("rev-parse", "--abbrev-ref", "HEAD")

    def git_branches(self) -> T.Set[str]:
        return set(self._git("branch", "--format=%(refname:short)").splitlines())

    def git_tags(self) -> T.Set[str]:
        return set(self._git("tag", "--list").splitlines())

    def tagged_commit(self, tag: str) -> str:
        return self.commit_of(tag)

    def commit_of(self, revision: str) -> str:
        return self._git("rev-parse", f"{revision}^{{commit}}")

    def git_ignores(self) -> T.List[str]:
        """Returns the lines of the .gitignore file of the repo."""
        path = self.repo_dir / ".gitignore"
        return path.read_text().splitlines() if path.exists() else []

    def groupy_branch_path(self, file_name: str) -> str:
        """Returns the path of a file in the per-branch dir of the current
        branch (e.g. .groupy/groupy-1/last-run.yaml)."""
        return f".groupy/{self.git_branch()}/{file_name}"

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
