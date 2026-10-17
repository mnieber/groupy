from apply_renamings_tests.apply_renamings_test_env import Context, TestEnv
from groupy.concepts.actions.add_alias import add_alias
from groupy.concepts.actions.set_concept import set_concept
from groupy.concepts.actions.set_local_term import set_local_term
from groupy.nodes.actions.set_rename_to import set_rename_to
from groupy.renamings.actions.set_renaming import set_renaming

STATS = "myapp/stats.py"
REPORTS = "myapp/reports.py"

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


class Sample:
    def __init__(self, points):
        self.pts = points

    def count_points(self):
        return len(self.pts)
"""

REPORTS_PY = """\
from myapp.stats import MAX_OUTLIERS, is_outlier_point


def describe(point):
    if is_outlier_point(point, MAX_OUTLIERS):
        return "outlier"
    return "normal"
"""

RENAMED_STATS_PY = """\
MAX_NR_OF_OUTLIERS = 10


def find_outliers(points, limit):
    new_outliers = []
    for point in points:
        if is_outlier(point, limit):
            new_outliers.append(point)
    return new_outliers[:MAX_NR_OF_OUTLIERS]


def is_outlier(point, threshold):
    return abs(point) > threshold


class Sample:
    def __init__(self, points):
        self.points = points

    def count(self):
        return len(self.points)
"""

RENAMED_REPORTS_PY = """\
from myapp.stats import MAX_NR_OF_OUTLIERS, is_outlier


def describe(point):
    if is_outlier(point, MAX_NR_OF_OUTLIERS):
        return "outlier"
    return "normal"
"""

OUTLIER = "a point that lies far from the other points"


def create_env(context: Context):
    return Env(context)


def test_apply_renamings_renames_symbols_and_nodes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # apply-renamings. Besides the modules of the base env, myapp has
    # stats.py and reports.py (which imports from stats.py). All modules are
    # in one chunk.
    if env.step(
        env.create_session_at_apply_renamings({STATS: STATS_PY, REPORTS: REPORTS_PY}),
    ):
        pass

    # The earlier stages (and the review of the developer) have left these
    # renamings in the node file of stats.py, for a module-level variable, a
    # local variable, a parameter, a function, a class attribute and a
    # method. find_outliers uses outlier_point as its concept (with the alias
    # outlier from its own name), and renames it to outlier, the name in the
    # glossary. outlier_point is not a symbol in its source.
    if env.step(
        env.edit_node_file(
            set_renaming, STATS, "@module", "MAX_OUTLIERS", "MAX_NR_OF_OUTLIERS"
        ),
        env.edit_node_file(
            set_concept, STATS, "find_outliers", "outlier_point", OUTLIER
        ),
        env.edit_node_file(
            add_alias, STATS, "find_outliers", "outlier_point", "outlier"
        ),
        env.edit_node_file(
            set_renaming, STATS, "find_outliers", "new_outlier_points", "new_outliers"
        ),
        env.edit_node_file(
            set_renaming, STATS, "find_outliers", "outlier_point", "outlier"
        ),
        env.edit_node_file(set_local_term, STATS, "is_outlier_point", "limit", None),
        env.edit_node_file(
            set_renaming, STATS, "is_outlier_point", "limit", "threshold"
        ),
        env.edit_node_file(set_rename_to, STATS, "is_outlier_point", "is_outlier"),
        env.edit_node_file(set_renaming, STATS, "Sample", "pts", "points"),
        env.edit_node_file(set_rename_to, STATS, "Sample.count_points", "count"),
        env.commit_all("review the renamings"),
        env.remember_git_head(),
    ):
        pass

    # We run groupy next.
    #
    # Groupy should have applied the renamings of stats.py and committed
    # them, and finished the chunk and the stage. The other modules have no
    # renamings, so they get no commit of their own.
    if env.step(
        env.run_groupy("next"),
    ):
        assert env.commit_messages_since_remembered_head() == [
            "apply-renamings: apply the renamings of myapp/stats.py",
            "apply-renamings: finish group-1/chunk-1",
            "apply-renamings: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the modules.
    #
    # The symbols should be renamed, including the import and the call sites
    # in reports.py.
    if env.step():
        assert env.read_module(STATS) == RENAMED_STATS_PY
        assert env.read_module(REPORTS) == RENAMED_REPORTS_PY

    # We look at the node file of stats.py.
    #
    # The nodes should have their new names, the concepts and local terms
    # should be renamed, and the renamings, rename_to and aliases should be
    # cleared.
    if env.step(
        env.load_module_node(STATS),
    ):
        assert env.module_node.renamings == {}
        assert env.names(env.module_node.variable_nodes) == ["MAX_NR_OF_OUTLIERS"]
        assert env.names(env.module_node.function_nodes) == [
            "find_outliers",
            "is_outlier",
        ]
        find_outliers_node = env.function_node("find_outliers")
        assert find_outliers_node.concepts == {"outlier": OUTLIER}
        assert find_outliers_node.aliases == {}
        assert find_outliers_node.renamings == {}
        is_outlier_node = env.function_node("is_outlier")
        assert is_outlier_node.local_terms == {"threshold": None}
        assert is_outlier_node.renamings == {}
        assert is_outlier_node.rename_to is None
        assert env.class_node("Sample").renamings == {}
        assert env.names(env.class_node("Sample").method_nodes) == [
            "__init__",
            "count",
        ]
        assert env.function_node("Sample.count").rename_to is None

    # We look at the session.
    #
    # The next stage should be extract-methods.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "extract-methods"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
