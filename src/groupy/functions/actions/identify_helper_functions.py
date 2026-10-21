from groupy.call_graph.actions.build_call_graph import build_call_graph
from groupy.call_graph.rules.get_call_graph_view import get_call_graph_view
from groupy.call_graph.rules.load_call_graph import load_call_graph
from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.functions.actions.mark_helper_candidates import mark_helper_candidates
from groupy.functions.actions.rename_helper_functions import rename_helper_functions
from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_active_chunks import get_active_chunks
from groupy.groups.rules.get_chunks import get_chunks
from groupy.renamings.rules.create_refactoring_policy import create_refactoring_policy
from groupy.sessions.actions.commit_stage_changes import commit_stage_changes
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.sessions.rules.get_exclude_patterns import get_exclude_patterns
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config

PROMPT = """\
Identify the helper functions in the modules of this chunk. A helper function only
exists to serve one other function (its parent) in the same module. The functions
that have exactly one caller in their module are marked as helper candidates
(is_helper_candidate in the node files), but not every candidate is a helper
function, and a function that is called from outside the module is never a helper
function. Take uncertain calls into account. Use the callback
move_function_to_parent to nest each helper function under its parent function.
"""


def identify_helper_functions() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    rfa_policy = create_rfa_policy(config)
    source_root = get_source_root()
    call_graph_path = get_branch_dir() / "call-graph.yaml"

    def _run_chunk(chunk: Chunk, rfa_id: str) -> None:
        # Mark the helper candidates
        build_call_graph(source_root, call_graph_path)
        call_graph = load_call_graph(call_graph_path)
        mark_helper_candidates(source_root, call_graph, chunk.module_names)
        commit_stage_changes("mark_helper_candidates")

        # Let Claude nest the helper functions, using the callers of each function
        view = get_call_graph_view(call_graph, source_root, chunk.module_names)
        for function_view in view.function_views:
            function_view.callees = []
        rfa_policy.run(Rfa(id=rfa_id, prompt=PROMPT, context={"call_graph_view": view}))

        # Rename the helper functions
        try:
            rename_helper_functions(
                source_root, chunk.module_names, create_refactoring_policy(config)
            )
        except BaseException:
            restore_working_tree()
            raise
        commit_stage_changes("rename_helper_functions")

    chunks = get_active_chunks(
        get_chunks(source_root, get_groupy_path("groups.txt"), config.max_chunk_lines),
        get_exclude_patterns(),
    )
    process_chunks(Stages.IDENTIFY_HELPER_FUNCTIONS, chunks, _run_chunk)
