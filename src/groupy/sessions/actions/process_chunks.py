import typing as T

from groupy.groups.models.chunk import Chunk
from groupy.sessions.actions.run_unfinished_step import run_unfinished_step
from groupy.sessions.enums import Stages
from groupy.utils.print_progress import print_progress


def process_chunks(
    stage: Stages,
    chunks: T.List[Chunk],
    run_chunk: T.Callable[[Chunk, str], None],
) -> None:
    for position, chunk in enumerate(chunks, start=1):

        def _run_chunk(request_id: str, chunk=chunk, position=position) -> None:
            # A finished chunk is skipped without a progress message
            print_progress(f"{request_id} ({position}/{len(chunks)})")
            run_chunk(chunk, request_id)

        run_unfinished_step(stage, chunk.id, _run_chunk)
