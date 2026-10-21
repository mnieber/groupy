from groupy.groups.models.chunk import Chunk
from groupy.groups.rules.get_active_chunks import get_active_chunks

CHUNKS = [
    Chunk(group_nr=1, nr=1, module_names=["myapp/books.py", "myapp/legacy.py"]),
    Chunk(group_nr=1, nr=2, module_names=["myapp/chapters.py"]),
    Chunk(group_nr=2, nr=1, module_names=["myapp/reports/summary.py"]),
    Chunk(group_nr=3, nr=1, module_names=["myapp/stats.py"]),
]


def test_get_active_chunks():
    # Without patterns, the chunks are unchanged
    assert get_active_chunks(CHUNKS, []) == CHUNKS

    # A chunk whose files are all passive is dropped, and the passive files are
    # removed from the other chunks
    active_chunks = get_active_chunks(CHUNKS, ["myapp/legacy.py", "myapp/reports/**"])
    assert [chunk.module_names for chunk in active_chunks] == [
        ["myapp/books.py"],
        ["myapp/chapters.py"],
        ["myapp/stats.py"],
    ]

    # The ids of the remaining chunks are unchanged
    assert [chunk.id for chunk in active_chunks] == [
        "group-1/chunk-1",
        "group-1/chunk-2",
        "group-3/chunk-1",
    ]

    # The chunks that are passed in are not changed
    assert CHUNKS[0].module_names == ["myapp/books.py", "myapp/legacy.py"]
