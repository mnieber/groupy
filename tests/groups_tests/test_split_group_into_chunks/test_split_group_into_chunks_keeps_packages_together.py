from groups_tests.groups_test_env import Context, TestEnv

MODULE_SIZES = {
    "myapp/books/__init__.py": 0,
    "myapp/books/create_book.py": 30,
    "myapp/books/delete_book.py": 30,
    "myapp/books/forms/book_form.py": 30,
    "myapp/books/forms/chapter_form.py": 50,
    "myapp/books/views/book_view.py": 20,
}


def create_env(context: Context):
    return Env(context)


def test_split_group_into_chunks_keeps_packages_together(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the books package (60 lines), with the sub-packages forms (80
    # lines) and views (20 lines).
    if env.step(
        env.add_modules(MODULE_SIZES),
    ):
        pass

    # We split group 2, which contains all these modules, into chunks of at
    # most 100 lines.
    #
    # The forms package does not fit in the chunk of the books package, so it
    # should start a new chunk (even though book_form.py would still fit). The
    # views package fits in the chunk of the forms package. The chunks should
    # be numbered per group.
    if env.step(
        env.split_group_into_chunks(
            sorted(MODULE_SIZES), max_chunk_lines=100, group_nr=2
        ),
    ):
        assert env.module_names_per_chunk() == {
            "group-2/chunk-1": [
                "myapp/books/__init__.py",
                "myapp/books/create_book.py",
                "myapp/books/delete_book.py",
            ],
            "group-2/chunk-2": [
                "myapp/books/forms/book_form.py",
                "myapp/books/forms/chapter_form.py",
                "myapp/books/views/book_view.py",
            ],
        }

    # We look at the group number and the chunk number of the chunks.
    #
    # They should match the chunk id.
    if env.step():
        assert [(chunk.group_nr, chunk.nr) for chunk in env.chunks] == [(2, 1), (2, 2)]
        chunks = env.module_names_per_chunk()

    # We split the same group again, with the modules in another order.
    #
    # We should get the same chunks, with the same ids.
    if env.step(
        env.split_group_into_chunks(
            sorted(MODULE_SIZES, reverse=True), max_chunk_lines=100, group_nr=2
        ),
    ):
        assert env.module_names_per_chunk() == chunks

    # We split a group that is smaller than the maximum chunk size.
    #
    # It should give a single chunk.
    if env.step(
        env.split_group_into_chunks(
            sorted(MODULE_SIZES), max_chunk_lines=1000, group_nr=3
        ),
    ):
        assert env.module_names_per_chunk() == {
            "group-3/chunk-1": sorted(MODULE_SIZES),
        }


class Env(TestEnv):
    pass
