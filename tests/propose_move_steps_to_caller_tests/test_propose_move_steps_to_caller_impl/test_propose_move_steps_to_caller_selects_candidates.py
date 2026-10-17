from propose_move_steps_to_caller_tests.propose_move_steps_to_caller_test_env import (
    Context,
    TestEnv,
)

RFA_ID = "propose-move-steps-to-caller/group-1/chunk-1"

STATS_PY = """\
class Sample:
    def __init__(self, points):
        self.points = points

    def summarize(self):
        return format_points(self.points)

    def save(self):
        pass


def format_points(points):
    return ", ".join(str(point) for point in points)


def count_points(points):
    return len(points)


def store(item):
    item.save()


def get_default_count():
    return 10


DEFAULT_COUNT = get_default_count()
"""

CHAPTER_STATS_PY = """\
from myapp.stats import count_points


def describe_chapter(chapter):
    return f"{count_points(chapter.points)} points"
"""


def create_env(context: Context):
    return Env(context)


def test_propose_move_steps_to_caller_selects_candidates(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-move-steps-to-caller. Besides the modules of the base env,
    # myapp has stats.py, and myapp/chapters has chapter_stats.py, which calls
    # count_points of stats.py. With the package grouping strategy, the
    # modules of myapp are in group-1, and the modules of myapp/chapters are
    # in group-2. The RFA of group-1 proposes nothing.
    if env.step(
        env.create_session_at_propose_move_steps_to_caller(
            {
                "myapp/stats.py": STATS_PY,
                "myapp/chapters/chapter_stats.py": CHAPTER_STATS_PY,
            }
        ),
        env.script_rfa(RFA_ID),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # The modules of myapp/chapters have no candidates (describe_chapter and
    # create_chapter have no callers), so group-2 should be finished without
    # an RFA.
    if env.step(
        env.run_breaker("next"),
    ):
        assert env.rfa_ids() == [RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            "propose-move-steps-to-caller: finish group-1/chunk-1",
            "propose-move-steps-to-caller: finish group-2/chunk-1",
            "propose-move-steps-to-caller: finish the stage",
        ]

    # We look at the candidates in the context of the RFA.
    #
    # A function or method should be a candidate when it has at least one
    # caller, and all its callers are functions or methods with certain
    # edges, also when a caller is a method or is in another chunk.
    if env.step():
        assert env.rfa(RFA_ID).context["move_step_candidates"] == [
            "myapp/books.py:Book.__init__",
            "myapp/books.py:_normalize_title",
            "myapp/stats.py:count_points",
            "myapp/stats.py:format_points",
        ]
        # Not candidates:
        # - Sample.__init__, Sample.summarize and store have no callers;
        # - Sample.save is called through an uncertain edge (by store);
        # - get_default_count is called from module-level code.

    # We look at the sources of the callers in the context of the RFA.
    #
    # They should contain the caller in another chunk, and the caller that is
    # a method (dedented, under its qualified name).
    if env.step():
        caller_sources = env.rfa(RFA_ID).context["caller_sources"]
        assert caller_sources["myapp/chapters/chapter_stats.py:describe_chapter"] == (
            "def describe_chapter(chapter):\n"
            '    return f"{count_points(chapter.points)} points"'
        )
        assert caller_sources["myapp/stats.py:Sample.summarize"] == (
            "def summarize(self):\n    return format_points(self.points)"
        )


class Env(TestEnv):
    pass
