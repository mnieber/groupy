from groupy.call_graph.actions.build_call_graph import build_call_graph
from groupy.call_graph.rules.get_call_graph_view import get_call_graph_view
from groupy.call_graph.rules.load_call_graph import load_call_graph
from groupy.claude_requests.actions.run_rfa_with_follow_up import run_rfa_with_follow_up
from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.concepts.rules.get_glossary_path import get_glossary_path
from groupy.concepts.rules.get_glossary_text import get_glossary_text
from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.rules.get_module_sources import get_module_sources
from groupy.nodes.rules.get_package_node_file_path import get_package_node_file_path
from groupy.nodes.rules.load_package_node import load_package_node
from groupy.restructure.actions.report_dependency_violations import (
    report_dependency_violations,
)
from groupy.restructure.rules.validate_code_restructure import validate_code_restructure
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config

PROMPT = """\
Propose where the code units of the modules of this chunk go, using the proposed
modules (feature packages). For every top-level function, class and module-level
variable, set its code_unit_type (set_code_unit_type) and, when it goes to another
file, its move_to_file (set_move_to_file). Set the rename_to of a module that
continues to exist (set_rename_to at @module). A method may delegate to a new action,
rule or util: set its code_unit_type and move_to_file. Follow these guidelines:
- an action changes the application state: <package>/actions/<name>.py
- a rule computes information subject to business logic: <package>/rules/<name>.py
- a util has no business logic: <package>/utils/<name>.py
- a model is a dataclass of a domain entity: <package>/models/<name>.py
- a schema describes a JSON blob: close to the code that uses it
- enums go to <package>/enums.py, settings to <app_package>/settings.py
- a constant goes to the file of the code unit that uses it
- an entrypoint goes to <app_package>/runtime/entrypoints/<name>.py
- an exception goes to the action file that raises it
- a policy is the interface to an external service: <package>/policies/<name>.py
Each action, rule, util and model gets a file of its own, and dependencies point in
one direction: entrypoints -> actions -> rules -> utils.
"""

FOLLOW_UP_PROMPT = """\
The proposed code restructure has the problems in restructure_problems. Please fix
them.
"""


def propose_code_restructure() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    rfa_policy = create_rfa_policy(config)
    source_root = get_source_root()
    call_graph_path = get_groupy_path("call-graph.yaml")

    def _run_chunk(chunk: Chunk, rfa_id: str) -> None:
        build_call_graph(source_root, call_graph_path)
        call_graph = load_call_graph(call_graph_path)
        root_package_node = load_package_node(
            get_package_node_file_path(source_root, ".")
        )
        rfa = Rfa(
            id=rfa_id,
            prompt=PROMPT,
            context={
                "module_sources": get_module_sources(source_root, chunk.module_names),
                "proposed_modules": root_package_node.proposed_modules,
                "call_graph_view": get_call_graph_view(
                    call_graph, source_root, chunk.module_names
                ),
                "glossary": get_glossary_text(get_glossary_path(source_root)),
            },
        )
        problems = run_rfa_with_follow_up(
            rfa_policy,
            rfa,
            lambda: validate_code_restructure(source_root, chunk.module_names),
            "restructure_problems",
            FOLLOW_UP_PROMPT,
        )
        if problems:
            raise CodeRestructureHasProblemsError(
                "The proposed code restructure has problems:\n" + "\n".join(problems)
            )

    chunks = get_chunks(
        source_root, get_groupy_path("groups.txt"), config.max_chunk_lines
    )
    process_chunks(Stages.PROPOSE_CODE_RESTRUCTURE, chunks, _run_chunk)
    report_dependency_violations(source_root, call_graph_path)


class CodeRestructureHasProblemsError(Exception):
    pass
