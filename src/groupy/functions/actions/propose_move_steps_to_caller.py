from groupy.call_graph.actions.build_call_graph import build_call_graph
from groupy.call_graph.rules.load_call_graph import load_call_graph
from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.functions.rules.get_caller_sources import get_caller_sources
from groupy.functions.rules.get_function_locations import get_function_locations
from groupy.functions.rules.is_move_step_candidate import is_move_step_candidate
from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_active_chunks import get_active_chunks
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.rules.get_module_sources import get_module_sources
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.sessions.rules.get_exclude_patterns import get_exclude_patterns
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config

PROMPT = """\
For the functions in move_step_candidates, identify the steps that should be done by
the callers of the function (before they call it), using the sources of the callers
in caller_sources. The steps of each candidate are in candidate_steps: pass a step to
a callback exactly as it is written there. Only propose to move a step when the function has a single caller,
or when all callers should clearly perform the step; otherwise moving the step would
duplicate code. Record each step that should move with add_step_to_move_to_caller.
Do not change the source.
"""


def propose_move_steps_to_caller() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    rfa_policy = create_rfa_policy(config)
    source_root = get_source_root()
    call_graph_path = get_branch_dir() / "call-graph.yaml"

    def _run_chunk(chunk: Chunk, rfa_id: str) -> None:
        build_call_graph(source_root, call_graph_path)
        call_graph = load_call_graph(call_graph_path)
        candidates = [
            (node_location, source_location, node)
            for node_location, source_location, node in get_function_locations(
                source_root, chunk.module_names
            )
            if is_move_step_candidate(call_graph, source_location)
        ]

        # A chunk without candidates is finished without an RFA
        if not candidates:
            return
        rfa_policy.run(
            Rfa(
                id=rfa_id,
                prompt=PROMPT,
                context={
                    "move_step_candidates": sorted(
                        node_location for node_location, _, _ in candidates
                    ),
                    "candidate_steps": {
                        node_location: node.steps
                        for node_location, _, node in candidates
                    },
                    "module_sources": get_module_sources(
                        source_root, chunk.module_names
                    ),
                    "caller_sources": get_caller_sources(
                        source_root,
                        call_graph,
                        [source_location for _, source_location, _ in candidates],
                    ),
                },
            )
        )

    chunks = get_active_chunks(
        get_chunks(source_root, get_groupy_path("groups.txt"), config.max_chunk_lines),
        get_exclude_patterns(),
    )
    process_chunks(Stages.PROPOSE_MOVE_STEPS_TO_CALLER, chunks, _run_chunk)
