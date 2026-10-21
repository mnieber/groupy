from propose_module_layout_tests.propose_module_layout_test_env import Context, TestEnv

RFA_ID = "propose-module-layout/all"

SUMMARY_PY = """\
def summarize(title):
    return title
"""


def create_env(context: Context):
    return Env(context)


def test_propose_module_layout_leaves_out_the_passive_modules(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-module-layout. Besides the modules of the base env, myapp has the
    # reports package, which the developer excludes.
    if env.step(
        env.create_session_at_propose_module_layout(
            {"myapp/reports/__init__.py": "", "myapp/reports/summary.py": SUMMARY_PY}
        ),
        env.set_session_exclude("myapp/reports/**"),
        env.script_rfa(RFA_ID),
    ):
        pass

    # We run groupy next.
    #
    # The RFA should only have the summaries of the active modules, so that
    # the passive modules keep their location.
    if env.step(
        env.run_groupy("next"),
    ):
        assert set(env.rfa(RFA_ID).context["module_summaries"]) == {
            "myapp/__init__.py",
            "myapp/books.py",
            "myapp/chapters/__init__.py",
            "myapp/chapters/create_chapter.py",
        }


class Env(TestEnv):
    pass
