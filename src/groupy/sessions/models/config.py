from dataclassy import dataclass


@dataclass
class Config:
    rfa_policy: str = (
        "groupy.claude_requests.policies.claude_rfa_policy:ClaudeRfaPolicy"
    )
    rfr_policy: str = (
        "groupy.claude_requests.policies.claude_rfr_policy:ClaudeRfrPolicy"
    )
    grouping_policy: str = (
        "groupy.groups.policies.claude_grouping_policy:ClaudeGroupingPolicy"
    )
    refactoring_policy: str = (
        "groupy.renamings.policies.rope_refactoring_policy:RopeRefactoringPolicy"
    )
    grouping_strategy: str = "package"
    max_group_lines: int = 2000
    max_chunk_lines: int = 500
