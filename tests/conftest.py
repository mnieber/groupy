from pathlib import Path

# The test packages that are enabled, in the order in which the code is implemented
ENABLED_TEST_PACKAGES = [
    "nodes_tests",
    "package_nodes_tests",
    "functions_tests",
    "node_edits_tests",
    "glossary_tests",
    "groups_tests",
    "group_modules_tests",
    "call_graph_tests",
    "sessions_tests",
    "groupy_next_tests",
    "groupy_sync_tests",
    "groupy_status_tests",
    "groupy_reset_tests",
    "groupy_branches_tests",
    "claude_policies_tests",
    "identify_helper_functions_tests",
    "analyze_terminology_tests",
    "propose_renamings_tests",
    "apply_renamings_tests",
    "extract_methods_tests",
    "propose_move_steps_to_caller_tests",
    "apply_move_steps_to_caller_tests",
    "propose_module_layout_tests",
    "propose_code_restructure_tests",
    "apply_code_restructure_tests",
]

collect_ignore = [
    path.name
    for path in Path(__file__).parent.iterdir()
    if path.is_dir() and path.name.endswith("_tests")
    if path.name not in ENABLED_TEST_PACKAGES
]
