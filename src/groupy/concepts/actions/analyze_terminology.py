from groupy.call_graph.actions.build_call_graph import build_call_graph
from groupy.call_graph.rules.get_call_graph_view import get_call_graph_view
from groupy.call_graph.rules.load_call_graph import load_call_graph
from groupy.claude_requests.actions.run_rfa_with_follow_up import run_rfa_with_follow_up
from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.concepts.rules.find_unanalyzed_nodes import find_unanalyzed_nodes
from groupy.concepts.rules.get_glossary_path import get_glossary_path
from groupy.concepts.rules.get_glossary_text import get_glossary_text
from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_active_chunks import get_active_chunks
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.rules.get_module_sources import get_module_sources
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.actions.run_unfinished_step import run_unfinished_step
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_branch_dir import get_branch_dir
from groupy.sessions.rules.get_exclude_patterns import get_exclude_patterns
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config

PROMPT = """\
Analyze the terminology of the modules of this chunk, and update the node files with
callbacks. First set the concepts of each module (set_concept at @module). Then, for
each function, method and class node: set its concepts and local terms (set_concept,
set_local_term), add its responsibilities and steps (add_responsibility, add_step),
record aliases (add_alias) and abbreviations of local terms and of concepts without a
glossary entry (set_abbreviation), and set its extract_method_priority (high, medium,
low or n/a). Leave a description empty when it is already given elsewhere, unless the
meaning in this node is specific. Finally, update the project glossary with the
concepts of the chunk (add_glossary_entry, add_glossary_alias,
set_glossary_abbreviation). A concept with the same name as an entry, but another
meaning, gets an entry of its own.
"""

FOLLOW_UP_PROMPT = """\
The nodes in unanalyzed_nodes have no extract_method_priority yet. Please analyze
them, and set their extract_method_priority.
"""

CONSOLIDATION_PROMPT = """\
Consolidate the project glossary: merge entries that have the same meaning
(merge_glossary_entries), and make the abbreviations consistent
(set_glossary_abbreviation). Do not resolve names with several meanings.
"""


def analyze_terminology() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    rfa_policy = create_rfa_policy(config)
    source_root = get_source_root()
    glossary_path = get_glossary_path(source_root)
    call_graph_path = get_branch_dir() / "call-graph.yaml"

    def _run_chunk(chunk: Chunk, rfa_id: str) -> None:
        build_call_graph(source_root, call_graph_path)
        call_graph = load_call_graph(call_graph_path)
        rfa = Rfa(
            id=rfa_id,
            prompt=PROMPT,
            context={
                "module_sources": get_module_sources(source_root, chunk.module_names),
                "call_graph_view": get_call_graph_view(
                    call_graph, source_root, chunk.module_names
                ),
                "glossary": get_glossary_text(glossary_path),
            },
        )
        unanalyzed_nodes = run_rfa_with_follow_up(
            rfa_policy,
            rfa,
            lambda: find_unanalyzed_nodes(source_root, chunk.module_names),
            "unanalyzed_nodes",
            FOLLOW_UP_PROMPT,
        )
        if unanalyzed_nodes:
            raise UnanalyzedNodesError(
                "These nodes are not analyzed: " + ", ".join(unanalyzed_nodes)
            )

    def _consolidate_glossary(rfa_id: str) -> None:
        rfa_policy.run(
            Rfa(
                id=rfa_id,
                prompt=CONSOLIDATION_PROMPT,
                context={"glossary": get_glossary_text(glossary_path)},
            )
        )

    chunks = get_active_chunks(
        get_chunks(source_root, get_groupy_path("groups.txt"), config.max_chunk_lines),
        get_exclude_patterns(),
    )
    process_chunks(Stages.ANALYZE_TERMINOLOGY, chunks, _run_chunk)

    # The consolidation is recorded as a final chunk
    run_unfinished_step(
        Stages.ANALYZE_TERMINOLOGY, "consolidate-glossary", _consolidate_glossary
    )


class UnanalyzedNodesError(Exception):
    pass
