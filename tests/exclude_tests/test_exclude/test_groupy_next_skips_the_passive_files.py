from exclude_tests.exclude_test_env import Context, TestEnv

RFA_ID_1 = "identify-helper-functions/group-1/chunk-1"

RFA_ID_2 = "identify-helper-functions/group-2/chunk-1"


def create_env(context: Context):
    return Env(context)


def test_groupy_next_skips_the_passive_files(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that excludes the legacy module and the reports
    # package. The chunks are group-1/chunk-1 (the modules of myapp, of which
    # legacy.py is passive), group-2/chunk-1 (myapp/chapters) and
    # group-3/chunk-1 (myapp/reports, which is all passive). Only the RFAs of
    # the first two chunks have a script.
    if env.step(
        env.create_session_with_reports("myapp/legacy.py", "myapp/reports/**"),
        env.script_rfa(RFA_ID_1),
        env.script_rfa(RFA_ID_2),
    ):
        pass

    # We run groupy next (identify-helper-functions).
    #
    # Groupy should make an RFA for the first two chunks, but not for
    # group-3/chunk-1, whose files are all passive. The stage should finish.
    if env.step(
        env.run_groupy_next(),
        env.load_session(),
    ):
        assert env.rfa_ids() == [RFA_ID_1, RFA_ID_2]
        assert env.session.next_stage == "analyze-terminology"

    # We look at the RFA of the first chunk.
    #
    # Its call graph view should only contain the functions of the active
    # module books.py, and not those of the passive module legacy.py.
    if env.step():
        assert env.function_locations_in_context(RFA_ID_1) == {
            "myapp/books.py:Book.__init__",
            "myapp/books.py:create_book",
            "myapp/books.py:_normalize_title",
        }


class Env(TestEnv):
    def function_locations_in_context(self, rfa_id: str):
        view = self.rfa(rfa_id).context["call_graph_view"]
        return {function_view.location for function_view in view.function_views}
