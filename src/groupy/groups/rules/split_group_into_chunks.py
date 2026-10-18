import typing as T
from pathlib import Path

from groupy.groups.models.chunk import Chunk
from groupy.groups.models.group import Group
from groupy.nodes.rules.get_line_count_by_module_name import (
    get_line_count_by_module_name,
)


def split_group_into_chunks(
    source_root: Path, group: Group, max_chunk_lines: int
) -> T.List[Chunk]:
    module_names = sorted(group.module_names)
    line_count_by_module_name = get_line_count_by_module_name(source_root, module_names)

    # The modules of a package (the modules that are directly in the same dir)
    module_names_by_package_name: T.Dict[str, T.List[str]] = {}
    for module_name in module_names:
        package_name = str(Path(module_name).parent)
        module_names_by_package_name.setdefault(package_name, []).append(module_name)

    chunks: T.List[Chunk] = []
    chunk_lines = 0

    def _start_chunk():
        nonlocal chunk_lines
        chunks.append(Chunk(group_nr=group.nr, nr=len(chunks) + 1))
        chunk_lines = 0

    def _add_module(module_name: str):
        nonlocal chunk_lines
        chunks[-1].module_names.append(module_name)
        chunk_lines += line_count_by_module_name[module_name]

    for package_module_names in module_names_by_package_name.values():
        package_lines = sum(
            line_count_by_module_name[module_name]
            for module_name in package_module_names
        )

        # A package that does not fit in the current chunk starts a new chunk
        if not chunks or chunk_lines + package_lines > max_chunk_lines:
            if not chunks or chunks[-1].module_names:
                _start_chunk()

        # A package that is too large for a chunk is split by sorted path
        for module_name in package_module_names:
            line_count = line_count_by_module_name[module_name]
            if chunks[-1].module_names and chunk_lines + line_count > max_chunk_lines:
                _start_chunk()
            _add_module(module_name)
    return chunks
