import json
import typing as T

from groupy_next_tests.groupy_next_test_env import Context
from groupy_next_tests.groupy_next_test_env import TestEnv as GroupyNextTestEnv

__all__ = ["Context", "TestEnv"]


class TestEnv(GroupyNextTestEnv):
    # Actions

    def write_last_run(self, **fields: T.Any) -> None:
        """Writes the last-run file (which is excluded from git), as groupy
        next would leave it behind."""
        lines = [f"{field}: {value}" for field, value in fields.items()]
        self.write_file(".groupy/last-run.yaml", "\n".join(lines) + "\n")

    def write_claude_log(
        self, request_id: str, *costs: float, is_aborted: bool = False
    ) -> None:
        """Adds Claude sessions to the log of the request, as Claude Code
        writes them: one session per cost, and an aborted session (without a
        result) if is_aborted."""
        messages = []
        for cost in costs:
            messages.append({"type": "system", "subtype": "init"})
            messages.append(
                {"type": "result", "subtype": "success", "total_cost_usd": cost}
            )
        if is_aborted:
            messages.append({"type": "system", "subtype": "init"})
        path = self.repo_dir / ".groupy" / "logs" / f"{request_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as log_file:
            for message in messages:
                log_file.write(json.dumps(message) + "\n")
