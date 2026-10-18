from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.rules.get_module_names import get_module_names
from groupy.renamings.actions.apply_module_renamings import apply_module_renamings
from groupy.renamings.actions.propose_renamings import ProposedRenamingHasConflictError
from groupy.renamings.rules.create_refactoring_policy import create_refactoring_policy
from groupy.renamings.rules.validate_renamings import validate_renamings
from groupy.sessions.actions.commit_stage_changes import commit_stage_changes
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.actions.restore_working_tree import restore_working_tree
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config


def apply_renamings() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    refactoring_policy = create_refactoring_policy(config)
    source_root = get_source_root()

    # The developer may have edited the renamings, so they are checked again
    # before anything changes
    conflicts = validate_renamings(source_root, get_module_names(source_root))
    if conflicts:
        raise ProposedRenamingHasConflictError(
            "The proposed renamings have conflicts:\n" + "\n".join(conflicts)
        )

    def _run_chunk(chunk: Chunk, _request_id: str) -> None:
        for module_name in sorted(chunk.module_names):
            # A failed rename also undoes the renames of the module that succeeded
            try:
                has_renamings = apply_module_renamings(
                    source_root, module_name, refactoring_policy
                )
            except BaseException:
                restore_working_tree()
                raise
            if has_renamings:
                commit_stage_changes(f"apply the renamings of {module_name}")

    chunks = get_chunks(
        source_root, get_groupy_path("groups.txt"), config.max_chunk_lines
    )
    process_chunks(Stages.APPLY_RENAMINGS, chunks, _run_chunk)
