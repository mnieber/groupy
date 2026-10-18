import typing as T

from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.policies.rfa_policy import RfaPolicy


def run_rfa_with_follow_up(
    rfa_policy: RfaPolicy,
    rfa: Rfa,
    find_problems: T.Callable[[], T.List[str]],
    problems_key: str,
    follow_up_prompt: str,
) -> T.List[str]:
    # When Claude left problems, it gets one follow-up RFA that lists them.
    # Returns the problems that remain.
    rfa_policy.run(rfa)
    problems = find_problems()
    if not problems:
        return []
    rfa_policy.run(
        Rfa(
            id=f"{rfa.id}/retry-1",
            prompt=follow_up_prompt,
            context={**rfa.context, problems_key: problems},
        )
    )
    return find_problems()
