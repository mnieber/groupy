from apply_code_restructure_tests.apply_code_restructure_test_env import (
    BOOKS,
    CREATE_BOOK,
    Context,
    TestEnv,
)

REPORT = "myapp/reports/report.py"

REPORT_PY = """\
def create_report(title):
    return title
"""


def create_env(context: Context):
    return Env(context)


def test_apply_code_restructure_skips_the_passive_modules(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-code-restructure, with a valid proposal for the modules of the
    # base env. Besides the modules of the base env, myapp has
    # myapp/reports/report.py, which has no proposal (no code_unit_type), and
    # which the developer excludes.
    if env.step(
        env.create_session_at_apply_code_restructure({REPORT: REPORT_PY}),
        env.set_session_exclude("myapp/reports/**"),
    ):
        pass

    # We run groupy next.
    #
    # The validation should only check the active modules, so the passive
    # module does not need a code_unit_type. Groupy should apply the proposal
    # of the active modules, and leave the passive module as it is.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "done"
        assert not env.file_exists(f"src/{BOOKS}")
        assert env.file_exists(f"src/{CREATE_BOOK}")
        assert env.read_module(REPORT) == REPORT_PY


class Env(TestEnv):
    pass
