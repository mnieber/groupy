from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_active_chunks import get_active_chunks
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.rules.get_active_module_names import get_active_module_names
from groupy.nodes.rules.get_module_names import get_module_names
from groupy.nodes.rules.get_passive_module_names import get_passive_module_names
from groupy.renamings.rules.create_refactoring_policy import create_refactoring_policy
from groupy.restructure.actions.propose_code_restructure import (
    CodeRestructureHasProblemsError,
)
from groupy.restructure.actions.report_dependency_violations import (
    report_dependency_violations,
)
from groupy.restructure.actions.restructure_module import restructure_module
from groupy.restructure.rules.validate_code_restructure import validate_code_restructure
from groupy.sessions.actions.commit_stage_changes import commit_stage_changes
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.sessions.rules.get_exclude_patterns import get_exclude_patterns
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config


def apply_code_restructure() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    refactoring_policy = create_refactoring_policy(config)
    source_root = get_source_root()
    group_file_path = get_groupy_path("groups.txt")

    # The developer may have edited the proposal, so it is validated again before
    # anything changes. The restructured modules have no proposal left.
    exclude_patterns = get_exclude_patterns()
    module_names = get_module_names(source_root)
    problems = validate_code_restructure(
        source_root,
        get_active_module_names(module_names, exclude_patterns),
        get_passive_module_names(module_names, exclude_patterns),
    )
    if problems:
        raise CodeRestructureHasProblemsError(
            "The proposed code restructure has problems:\n" + "\n".join(problems)
        )
    report_dependency_violations(source_root, get_branch_dir() / "call-graph.yaml")

    def _run_chunk(chunk: Chunk, _request_id: str) -> None:
        for module_name in sorted(chunk.module_names):
            if not (source_root / module_name).exists():
                continue
            try:
                changed = restructure_module(
                    source_root, module_name, refactoring_policy, group_file_path
                )
            except BaseException:
                restore_working_tree()
                raise
            if changed:
                commit_stage_changes(f"restructure {module_name}")

    chunks = get_active_chunks(
        get_chunks(source_root, group_file_path, config.max_chunk_lines),
        exclude_patterns,
    )
    process_chunks(Stages.APPLY_CODE_RESTRUCTURE, chunks, _run_chunk)
