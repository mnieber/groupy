import typing as T
from pathlib import Path

from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.load_group_file import load_group_file
from groupy.groups.rules.split_group_into_chunks import split_group_into_chunks


def get_chunks(
    source_root: Path, group_file_path: Path, max_chunk_lines: int
) -> T.List[Chunk]:
    return [
        chunk
        for group in load_group_file(group_file_path)
        for chunk in split_group_into_chunks(source_root, group, max_chunk_lines)
    ]
