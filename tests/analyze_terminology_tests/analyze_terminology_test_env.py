import re
import typing as T

import yaml
from breaker.claude_requests.models.callback import Callback
from breaker.claude_requests.models.rfa import Rfa
from breaker.concepts.models.glossary import Glossary
from breaker.concepts.rules.load_glossary import load_glossary
from breaker.nodes.models.module_node import ModuleNode
from breaker.nodes.rules.load_module_node import load_module_node
from breaker_next_tests.breaker_next_test_env import Context
from breaker_next_tests.breaker_next_test_env import TestEnv as BreakerNextTestEnv
from breaker_next_tests.breaker_next_test_env import callback

__all__ = ["Context", "TestEnv"]

STAGE = "analyze-terminology"

CONSOLIDATION_RFA_ID = "analyze-terminology/consolidate-glossary"

CHAPTER_TITLES_PY = """\
def number_heading(heading, nr):
    chapter_title = f"{nr}. {heading}"
    return chapter_title
"""


class TestEnv(BreakerNextTestEnv):
    """A TestEnv for the analyze-terminology stage. The target code (in the
    src dir) has the modules of the base env plus myapp/chapters/
    chapter_titles.py. With the package grouping strategy, the chunk
    group-1/chunk-1 has myapp/__init__.py and myapp/books.py, and the chunk
    group-2/chunk-1 has the modules of myapp/chapters."""

    def __init__(self, context: Context):
        self.source_root = context.repo_dir / "src"
        self.module_node: ModuleNode = None
        self.glossary: Glossary = None
        super().__init__(context)

    # Actions

    def create_session_at_analyze_terminology(
        self, grouping_strategy: str = "package"
    ) -> None:
        """Creates a session (that uses the fake RFA policy) whose next stage
        is analyze-terminology."""
        self.create_session(
            {"myapp/chapters/chapter_titles.py": CHAPTER_TITLES_PY},
            grouping_strategy=grouping_strategy,
            max_group_lines=10000,
            max_chunk_lines=10000,
        )
        self.set_next_stage(STAGE)

    def set_next_stage(self, stage_id: str) -> None:
        """Sets next_stage in the session file, and commits it (as if the
        earlier stages have run)."""
        session_path = ".breaker/session.yaml"
        text = self.read_file(session_path)
        self.write_file(
            session_path,
            re.sub(r"^next_stage: .*$", f"next_stage: {stage_id}", text, flags=re.M),
        )
        self.commit_all(f"start at {stage_id}")

    def catch_error(self, env_action: T.Callable, *args, **kwargs) -> None:
        """Runs the env action and stores the exception it is expected to
        raise in env.error."""
        self.error = None
        try:
            env_action(*args, **kwargs)
        except Exception as error:
            self.error = error

    def load_module_node(self, module_name: str) -> None:
        self.module_node = load_module_node(
            self.source_root / f"{module_name}.breaker.yaml"
        )

    def load_glossary(self) -> None:
        self.glossary = load_glossary(self.source_root / "glossary.breaker.yaml")

    # Queries (for use in asserts)

    def rfa(self, rfa_id: str) -> Rfa:
        matches = [rfa for rfa in self.rfa_policy().requests if rfa.id == rfa_id]
        assert len(matches) == 1, f"Expected one RFA with the id {rfa_id}"
        return matches[0]

    def glossary_entries_in_context(self, rfa_id: str) -> T.List[T.Tuple[str, str]]:
        """Returns the (name, description) pairs of the glossary in the
        context of the RFA."""
        entries = yaml.safe_load(self.rfa(rfa_id).context["glossary"]) or []
        return [(entry["name"], entry["description"]) for entry in entries]

    def callees_in_context(self, rfa_id: str, location: str) -> T.Set[T.Tuple]:
        """Returns the (callee, scope) pairs of the function view at the
        location, in the call graph view in the context of the RFA."""
        view = self.rfa(rfa_id).context["call_graph_view"]
        matches = [v for v in view.function_views if v.location == location]
        assert len(matches) == 1, f"Expected one function view for {location}"
        return {(call.location, call.scope) for call in matches[0].callees}

    def glossary_entries(self) -> T.List[T.Tuple[str, str, T.List[str]]]:
        """Returns the (name, description, aliases) triples of env.glossary."""
        return [
            (entry.name, entry.description, entry.aliases)
            for entry in self.glossary.entries
        ]

    def function_node(self, location: str):
        """Returns the function node or method node at the location (e.g.
        `create_book` or `Book.__init__`)."""
        if "." in location:
            class_name, method_name = location.split(".")
            class_node = _find_by_name(self.module_node.class_nodes, class_name)
            return _find_by_name(class_node.method_nodes, method_name)
        return _find_by_name(self.module_node.function_nodes, location)


def priority_callbacks(module_name: str, *locations: str) -> T.List[Callback]:
    """Returns the callbacks that set the extract_method_priority of the
    nodes at the locations to n/a."""
    return [
        callback(
            "set_extract_method_priority",
            module_name=module_name,
            location=location,
            priority="n/a",
        )
        for location in locations
    ]


def commit_messages(callbacks: T.List[Callback]) -> T.List[str]:
    """Returns the messages of the commits that Breaker makes after running
    the callbacks."""
    return [f"{STAGE}: {callback.name}" for callback in callbacks]


def _find_by_name(nodes: T.List[T.Any], name: str):
    matches = [node for node in nodes if node.name == name]
    assert len(matches) == 1, f"Expected one node called {name}"
    return matches[0]
