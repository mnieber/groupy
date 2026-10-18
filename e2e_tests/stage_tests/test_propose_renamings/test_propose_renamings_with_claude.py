from stage_tests.e2e_test_env import Context, TestEnv

from groupy.concepts.actions.add_alias import add_alias

STATS = "myapp/stats.py"

STATS_PY = """\
def find_outliers(points, limit):
    new_outlier_points = []
    for point in points:
        if is_outlier_point(point, limit):
            new_outlier_points.append(point)
    return new_outlier_points


def is_outlier_point(point, limit):
    return abs(point) > limit
"""

GLOSSARY_YAML = """\
- name: outlier
  description: a point that lies far from the other points
  aliases: [outlier_point]
"""


def create_env(context: Context):
    return Env(context)


def test_propose_renamings_with_claude(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session that uses Claude, whose next stage is
    # propose-renamings. The module stats.py uses outlier_point as an alias of
    # outlier, which the node files and the glossary record.
    if env.step(
        env.create_session_with_claude({STATS: STATS_PY}),
        env.write_glossary(GLOSSARY_YAML),
        env.edit_node_file(
            add_alias, STATS, "find_outliers", "outlier", "outlier_point"
        ),
        env.edit_node_file(
            add_alias, STATS, "is_outlier_point", "outlier", "outlier_point"
        ),
        env.set_next_stage("propose-renamings"),
    ):
        pass

    # We run groupy next.
    #
    # Claude should have proposed renamings without conflicts, so that the
    # stage finished with a clean working tree. Claude may not edit the
    # source in an RFA.
    if env.step(
        env.run_groupy("next"),
        env.load_session(),
    ):
        assert env.session.next_stage == "apply-renamings"
        assert env.git_status() == ""
        assert env.read_module(STATS) == STATS_PY

    # We look at the node file of stats.py.
    #
    # Claude should have proposed to rename is_outlier_point and
    # new_outlier_points to names without the alias outlier_point.
    if env.step(
        env.load_module_node(STATS),
    ):
        new_name = env.function_node("is_outlier_point").rename_to
        assert new_name and "outlier_point" not in new_name
        renamings = env.function_node("find_outliers").renamings
        assert "new_outlier_points" in renamings
        assert "outlier_point" not in renamings["new_outlier_points"]


class Env(TestEnv):
    pass
