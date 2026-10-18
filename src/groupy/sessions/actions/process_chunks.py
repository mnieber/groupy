import typing as T

from groupy.groups.models.chunk import Chunk
from groupy.sessions.actions.run_unfinished_step import run_unfinished_step
from groupy.sessions.enums import Stages


def process_chunks(
    stage: Stages,
    chunks: T.List[Chunk],
    run_chunk: T.Callable[[Chunk, str], None],
) -> None:
    for chunk in chunks:
        run_unfinished_step(
            stage, chunk.id, lambda request_id: run_chunk(chunk, request_id)
        )
