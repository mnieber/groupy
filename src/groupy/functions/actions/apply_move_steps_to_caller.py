import typing as T

from groupy.call_graph.actions.build_call_graph import build_call_graph
from groupy.call_graph.rules.load_call_graph import load_call_graph
from groupy.claude_requests.models.rfr import Rfr
from groupy.claude_requests.rules.create_rfr_policy import create_rfr_policy
from groupy.functions.rules.find_steps_to_move import find_steps_to_move
from groupy.functions.rules.get_caller_sources import get_caller_sources
from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.rules.get_module_sources import get_module_sources
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config
from groupy.utils.run_git import run_git

PROMPT = """\
Move the steps in steps_to_move_to_caller from their function to the callers of the
function (see caller_sources). For each move: edit the source, remove the step from
the function (remove_step), add it to the steps of the callers (add_step), and call
commit_refactoring with a short description. When a step cannot be moved after all,
withdraw the proposal with remove_step_to_move_to_caller.
"""

FOLLOW_UP_PROMPT = """\
The steps in steps_to_move_to_caller are not moved yet. Please move them (and call
commit_refactoring after each move), or withdraw the proposals with
remove_step_to_move_to_caller.
"""


def apply_move_steps_to_caller() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    rfr_policy = create_rfr_policy(config)
    source_root = get_source_root()
    call_graph_path = get_groupy_path("call-graph.yaml")

    def _find_lines(chunk: Chunk) -> T.List[str]:
        return [
            f"{node_location}: {step}"
            for node_location, _, step in find_steps_to_move(
                source_root, chunk.module_names
            )
        ]

    def _run_rfr(rfr: Rfr) -> None:
        # Claude commits its work with commit_refactoring, so uncommitted changes
        # are an unfinished refactoring
        try:
            rfr_policy.run(rfr)
        except Exception:
            restore_working_tree()
            raise
        if run_git("status", "--porcelain"):
            restore_working_tree()
            raise UncommittedRefactoringError(
                f"The RFR {rfr.id} left uncommitted changes, which were discarded"
            )

    def _run_chunk(chunk: Chunk, rfr_id: str) -> None:
        # A chunk without steps to move is finished without an RFR
        steps_to_move = find_steps_to_move(source_root, chunk.module_names)
        if not steps_to_move:
            return

        build_call_graph(source_root, call_graph_path)
        call_graph = load_call_graph(call_graph_path)
        context = {
            "steps_to_move_to_caller": _find_lines(chunk),
            "module_sources": get_module_sources(source_root, chunk.module_names),
            "caller_sources": get_caller_sources(
                source_root,
                call_graph,
                [source_location for _, source_location, _ in steps_to_move],
            ),
        }
        _run_rfr(Rfr(id=rfr_id, prompt=PROMPT, context=context))

        # The steps that are not moved get one follow-up RFR
        if _find_lines(chunk):
            _run_rfr(
                Rfr(
                    id=f"{rfr_id}/retry-1",
                    prompt=FOLLOW_UP_PROMPT,
                    context={**context, "steps_to_move_to_caller": _find_lines(chunk)},
                )
            )
        unapplied_moves = _find_lines(chunk)
        if unapplied_moves:
            raise UnappliedStepMovesError(
                "These steps are not moved: " + ", ".join(unapplied_moves)
            )

    chunks = get_chunks(
        source_root, get_groupy_path("groups.txt"), config.max_chunk_lines
    )
    process_chunks(Stages.APPLY_MOVE_STEPS_TO_CALLER, chunks, _run_chunk)


class UncommittedRefactoringError(Exception):
    pass


class UnappliedStepMovesError(Exception):
    pass
