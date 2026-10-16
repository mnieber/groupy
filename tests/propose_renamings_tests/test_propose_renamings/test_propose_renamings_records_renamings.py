from breaker_next_tests.breaker_next_test_env import callback
from propose_renamings_tests.propose_renamings_test_env import (
    RFA_ID,
    Context,
    TestEnv,
    commit_messages,
)

STATS = "myapp/stats.py"

STATS_PY = """\
MAX_OUTLIERS = 10


def find_outliers(points, limit):
    new_outlier_points = []
    for point in points:
        if is_outlier_point(point, limit):
            new_outlier_points.append(point)
    return new_outlier_points[:MAX_OUTLIERS]


def is_outlier_point(point, limit):
    return abs(point) > limit
"""

GLOSSARY_YAML = """\
- name: outlier
  description: a point that lies far from the other points
  aliases: [outlier_point]
"""

# The callbacks of the RFA. They replace the alias outlier_point by the
# canonical name outlier, and make MAX_OUTLIERS more explicit.
CALLBACKS = [
    callback(
        "set_renaming",
        module_name=STATS,
        location="find_outliers",
        name="new_outlier_points",
        new_name="new_outliers",
    ),
    callback(
        "set_rename_to",
        module_name=STATS,
        location="is_outlier_point",
        new_name="is_outlier",
    ),
    callback(
        "set_renaming",
        module_name=STATS,
        location="@module",
        name="MAX_OUTLIERS",
        new_name="MAX_NR_OF_OUTLIERS",
    ),
]


def create_env(context: Context):
    return Env(context)


def test_propose_renamings_records_renamings(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # propose-renamings. Besides the modules of the base env, myapp has
    # stats.py, which uses outlier_point as an alias of outlier. The glossary
    # lists outlier_point as an alias of outlier. All modules are in one
    # chunk, and its RFA is scripted.
    if env.step(
        env.create_session_at_propose_renamings({STATS: STATS_PY}, GLOSSARY_YAML),
        env.script_rfa(RFA_ID, *CALLBACKS),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # Breaker should have made the RFA of the chunk, committed after each
    # callback, and finished the chunk and the stage.
    if env.step(
        env.run_breaker("next"),
    ):
        assert env.rfa_ids() == [RFA_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(CALLBACKS),
            "propose-renamings: finish group-1/chunk-1",
            "propose-renamings: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the context of the RFA.
    #
    # It should contain the source of the modules of the chunk and the
    # glossary.
    if env.step():
        context = env.rfa(RFA_ID).context
        assert context["module_sources"][STATS] == STATS_PY
        assert context["glossary"] == GLOSSARY_YAML

    # We look at the node file of stats.py.
    #
    # The renamings should be recorded in the nodes of their scope.
    if env.step(
        env.load_module_node(STATS),
    ):
        assert env.function_node("find_outliers").renamings == {
            "new_outlier_points": "new_outliers"
        }
        assert env.function_node("is_outlier_point").rename_to == "is_outlier"
        assert env.module_node.renamings == {"MAX_OUTLIERS": "MAX_NR_OF_OUTLIERS"}

    # We look at stats.py and the session.
    #
    # The renamings are only proposed, so the source should be unchanged. The
    # next stage should be apply-renamings.
    if env.step(
        env.load_session(),
    ):
        assert env.read_module(STATS) == STATS_PY
        assert env.session.next_stage == "apply-renamings"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
