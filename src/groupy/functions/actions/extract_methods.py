from groupy.claude_requests.actions.run_rfa_with_follow_up import run_rfa_with_follow_up
from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.functions.actions.rename_helper_functions import rename_helper_functions
from groupy.functions.rules.find_extract_method_candidates import (
    find_extract_method_candidates,
)
from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_active_chunks import get_active_chunks
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.rules.get_module_sources import get_module_sources
from groupy.renamings.rules.create_refactoring_policy import create_refactoring_policy
from groupy.sessions.actions.commit_stage_changes import commit_stage_changes
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_exclude_patterns import get_exclude_patterns
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config

PROMPT = """\
The functions in extract_method_candidates have too many responsibilities. For each
candidate, call extract_method(module_name, location, new_name, description) for each
part that should become a function of its own. Fill in the analysis of each
extracted function (e.g. its concepts, responsibilities and steps), update the
analysis of the original function, and nest an extracted function that is a helper
function with move_function_to_parent. A nested helper function keeps its name
until Groupy renames it after this request (e.g. validate becomes _validate), so use
its current name in the locations (e.g. create_report.validate). When you are done
with a candidate (also when you decide not to extract anything), set its
extract_method_priority to n/a.
"""

FOLLOW_UP_PROMPT = """\
The candidates in unfinished_candidates still have the priority high or medium.
Please finish them, and set their extract_method_priority to n/a.
"""


def extract_methods() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    rfa_policy = create_rfa_policy(config)
    source_root = get_source_root()

    def _run_chunk(chunk: Chunk, rfa_id: str) -> None:
        # A chunk without candidates is finished without an RFA
        candidates = find_extract_method_candidates(source_root, chunk.module_names)
        if not candidates:
            return

        rfa = Rfa(
            id=rfa_id,
            prompt=PROMPT,
            context={
                "extract_method_candidates": candidates,
                "module_sources": get_module_sources(source_root, chunk.module_names),
            },
        )
        unfinished_candidates = run_rfa_with_follow_up(
            rfa_policy,
            rfa,
            lambda: find_extract_method_candidates(source_root, chunk.module_names),
            "unfinished_candidates",
            FOLLOW_UP_PROMPT,
        )
        if unfinished_candidates:
            raise UnfinishedCandidatesError(
                "These candidates are not finished: " + ", ".join(unfinished_candidates)
            )

        # Rename the extracted functions that Claude nested as helper functions
        try:
            renamed = rename_helper_functions(
                source_root, chunk.module_names, create_refactoring_policy(config)
            )
        except BaseException:
            restore_working_tree()
            raise
        if renamed:
            commit_stage_changes("rename_helper_functions")

    chunks = get_active_chunks(
        get_chunks(source_root, get_groupy_path("groups.txt"), config.max_chunk_lines),
        get_exclude_patterns(),
    )
    process_chunks(Stages.EXTRACT_METHODS, chunks, _run_chunk)


class UnfinishedCandidatesError(Exception):
    pass
