from breaker.functions.actions.set_extract_method_priority import (
    set_extract_method_priority,
)
from groupy_next_tests.groupy_next_test_env import callback, file_write
from extract_methods_tests.extract_methods_test_env import (
    Context,
    TestEnv,
    commit_messages,
)

REPORTS = "myapp/reports.py"

RFA_ID = "extract-methods/group-1/chunk-1"
RFR_ID = "extract_method/myapp/reports.py:create_report/format_stats"

REPORTS_PY = """\
def create_report(user):
    lines = []
    for stat in user.stats:
        lines.append(f"{stat.name}: {stat.value}")
    header = user.name.upper()
    return header + "\\n" + "\\n".join(lines)


def send_report(user):
    return create_report(user)
"""

# The text of reports.py that the RFR writes.
EXTRACTED_REPORTS_PY = """\
def create_report(user):
    lines = format_stats(user.stats)
    header = user.name.upper()
    return header + "\\n" + "\\n".join(lines)


def format_stats(stats):
    lines = []
    for stat in stats:
        lines.append(f"{stat.name}: {stat.value}")
    return lines


def send_report(user):
    return create_report(user)
"""

# The text of reports.py after Breaker renamed the helper function.
RENAMED_REPORTS_PY = """\
def create_report(user):
    lines = _format_stats(user.stats)
    header = user.name.upper()
    return header + "\\n" + "\\n".join(lines)


def _format_stats(stats):
    lines = []
    for stat in stats:
        lines.append(f"{stat.name}: {stat.value}")
    return lines


def send_report(user):
    return create_report(user)
"""

# The callbacks of the RFA. They extract format_stats from create_report,
# fill in the analysis of format_stats, nest it under create_report, update
# the analysis of create_report, and mark create_report as done.
CALLBACKS = [
    callback(
        "extract_method",
        module_name=REPORTS,
        location="create_report",
        new_name="format_stats",
        description="Format the stats of the user as lines",
    ),
    callback(
        "add_responsibility",
        module_name=REPORTS,
        location="format_stats",
        responsibility="Formats stats as lines",
    ),
    callback(
        "set_extract_method_priority",
        module_name=REPORTS,
        location="format_stats",
        priority="n/a",
    ),
    callback(
        "move_function_to_parent",
        module_name=REPORTS,
        function_location="format_stats",
        parent_location="create_report",
    ),
    callback(
        "add_step",
        module_name=REPORTS,
        location="create_report",
        step="Format the stats",
    ),
    callback(
        "set_extract_method_priority",
        module_name=REPORTS,
        location="create_report",
        priority="n/a",
    ),
]


def create_env(context: Context):
    return Env(context)


def test_extract_methods_extracts_a_helper_function(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a session for the myapp package, whose next stage is
    # extract-methods. Besides the modules of the base env, myapp has
    # reports.py, where create_report has a high extract-method priority.
    # With the package grouping strategy, reports.py is in group-1, and the
    # modules of myapp/chapters (which have no candidates) are in group-2. The
    # RFA of group-1 and the RFR of the extraction are scripted.
    if env.step(
        env.create_session_at_extract_methods(
            {REPORTS: REPORTS_PY}, grouping_strategy="package"
        ),
        env.edit_node_file(
            set_extract_method_priority, REPORTS, "create_report", "high"
        ),
        env.edit_node_file(set_extract_method_priority, REPORTS, "send_report", "n/a"),
        env.commit_all("analyze the terminology"),
        env.script_rfa(RFA_ID, *CALLBACKS),
        env.script_rfr(RFR_ID, file_write(REPORTS, EXTRACTED_REPORTS_PY)),
        env.remember_git_head(),
    ):
        pass

    # We run breaker next.
    #
    # Breaker should have made an RFA for group-1 only, run the callbacks
    # (where extract_method made the RFR), renamed the new helper function,
    # and finished both chunks and the stage.
    if env.step(
        env.run_breaker("next"),
    ):
        assert env.rfa_ids() == [RFA_ID]
        assert env.rfr_ids() == [RFR_ID]
        assert env.commit_messages_since_remembered_head() == [
            *commit_messages(CALLBACKS),
            "extract-methods: rename_helper_functions",
            "extract-methods: finish group-1/chunk-1",
            "extract-methods: finish group-2/chunk-1",
            "extract-methods: finish the stage",
        ]
        assert env.git_status() == ""

    # We look at the context of the RFA and the RFR.
    #
    # The RFA should list the candidates, and the RFR should describe the
    # extraction.
    if env.step():
        rfa_context = env.rfa(RFA_ID).context
        assert rfa_context["extract_method_candidates"] == [
            "myapp/reports.py:create_report"
        ]
        assert rfa_context["module_sources"][REPORTS] == REPORTS_PY
        rfr_context = env.rfr(RFR_ID).context
        assert rfr_context["module_name"] == REPORTS
        assert rfr_context["location"] == "create_report"
        assert rfr_context["new_name"] == "format_stats"
        assert rfr_context["description"] == "Format the stats of the user as lines"

    # We look at reports.py.
    #
    # It should have the extracted function, renamed to start with an
    # underscore because Claude nested it.
    if env.step():
        assert env.read_module(REPORTS) == RENAMED_REPORTS_PY

    # We look at the node file of reports.py.
    #
    # The extracted function should be a helper function node of
    # create_report, with its analysis.
    if env.step(
        env.load_module_node(REPORTS),
    ):
        assert env.names(env.module_node.function_nodes) == [
            "create_report",
            "send_report",
        ]
        create_report_node = env.function_node("create_report")
        assert env.names(create_report_node.helper_function_nodes) == ["_format_stats"]
        assert create_report_node.steps == ["Format the stats"]
        assert create_report_node.extract_method_priority == "n/a"
        format_stats_node = env.function_node("create_report._format_stats")
        assert format_stats_node.responsibilities == ["Formats stats as lines"]
        assert format_stats_node.extract_method_priority == "n/a"

    # We look at the session.
    #
    # The next stage should be propose-move-steps-to-caller.
    if env.step(
        env.load_session(),
    ):
        assert env.session.next_stage == "propose-move-steps-to-caller"
        assert env.session.finished_chunks == []


class Env(TestEnv):
    pass
