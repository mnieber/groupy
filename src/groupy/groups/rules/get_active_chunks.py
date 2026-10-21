import typing as T

from groupy.groups.models.chunk import Chunk
from groupy.nodes.rules.get_active_module_names import get_active_module_names


def get_active_chunks(
    chunks: T.List[Chunk], exclude_patterns: T.List[str]
) -> T.List[Chunk]:
    # The chunks without their passive files. A chunk whose files are all passive is
    # dropped. The chunk ids stay the same.
    result = []
    for chunk in chunks:
        module_names = get_active_module_names(chunk.module_names, exclude_patterns)
        if module_names:
            result.append(
                Chunk(group_nr=chunk.group_nr, nr=chunk.nr, module_names=module_names)
            )
    return result
