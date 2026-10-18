from groupy.claude_requests.actions.run_rfa_with_follow_up import (
    run_rfa_with_follow_up,
)
from groupy.claude_requests.models.rfa import Rfa
from groupy.claude_requests.rules.create_rfa_policy import create_rfa_policy
from groupy.concepts.rules.get_glossary_path import get_glossary_path
from groupy.concepts.rules.get_glossary_text import get_glossary_text
from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_chunks import get_chunks
from groupy.nodes.rules.get_module_sources import get_module_sources
from groupy.renamings.rules.validate_renamings import validate_renamings
from groupy.sessions.actions.process_chunks import process_chunks
from groupy.sessions.enums import Stages
from groupy.sessions.rules.get_groupy_path import get_groupy_path
from groupy.sessions.rules.get_source_root import get_source_root
from groupy.sessions.rules.load_config import load_config

PROMPT = """\
Propose renamings that replace the aliases in the node files of this chunk by their
canonical names, preferably the names of the glossary. Record a renaming of a local
symbol, concept or local term with set_renaming at the function, of an attribute at
the class, and of a module-level symbol at @module. Record a new name for a function,
class or variable with set_rename_to. A renaming maps an entire symbol onto its new
name, and keeps its meaning (e.g. plural stays plural). Name a map foo_by_bar, where
foo is the value and bar the key. You may use the abbreviations of the glossary, and
the abbreviations in the node of a function within that function, but do not
introduce new abbreviations. Only rename symbols that are defined in the target code.
"""

FOLLOW_UP_PROMPT = """\
The proposed renamings have the conflicts in renaming_conflicts. Please resolve them
(with set_renaming, remove_renaming and set_rename_to).
"""


def propose_renamings() -> None:
    config = load_config(get_groupy_path("config.yaml"))
    rfa_policy = create_rfa_policy(config)
    source_root = get_source_root()

    def _run_chunk(chunk: Chunk, rfa_id: str) -> None:
        rfa = Rfa(
            id=rfa_id,
            prompt=PROMPT,
            context={
                "module_sources": get_module_sources(source_root, chunk.module_names),
                "glossary": get_glossary_text(get_glossary_path(source_root)),
            },
        )
        conflicts = run_rfa_with_follow_up(
            rfa_policy,
            rfa,
            lambda: validate_renamings(source_root, chunk.module_names),
            "renaming_conflicts",
            FOLLOW_UP_PROMPT,
        )
        if conflicts:
            raise ProposedRenamingHasConflictError(
                "The proposed renamings have conflicts:\n" + "\n".join(conflicts)
            )

    chunks = get_chunks(
        source_root, get_groupy_path("groups.txt"), config.max_chunk_lines
    )
    process_chunks(Stages.PROPOSE_RENAMINGS, chunks, _run_chunk)


class ProposedRenamingHasConflictError(Exception):
    pass
