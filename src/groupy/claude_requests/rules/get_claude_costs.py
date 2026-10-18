import json

from groupy.claude_requests.models.claude_costs import ClaudeCosts
from groupy.sessions.rules.get_groupy_path import get_groupy_path


def get_claude_costs() -> ClaudeCosts:
    # Sums the costs of the Claude sessions in the logs. A session starts with an
    # init message, and a session that finished ends with a result that has its
    # cost. Without a result, the cost of the session is unknown.
    costs = ClaudeCosts()
    for log_path in sorted(get_groupy_path("logs").rglob("*.jsonl")):
        nr_of_sessions = 0
        nr_of_results = 0
        for line in log_path.read_text().splitlines():
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("type") == "system" and message.get("subtype") == "init":
                nr_of_sessions += 1
            elif message.get("type") == "result" and "total_cost_usd" in message:
                nr_of_results += 1
                costs.total_usd += message["total_cost_usd"]
        if nr_of_results < nr_of_sessions:
            costs.is_complete = False
    return costs
