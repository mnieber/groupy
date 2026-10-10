from load_and_save_module_node_tests.node_file_test_env import Context, TestEnv

# A node file in the format that Breaker writes: the fields are in the order of
# the schema, and fields that have their default value are left out.
MARKDOWN_REPORTS_NODE_YAML = """\
module_node:
  name: reports/markdown_reports.py
  rename_to: reports/rules/create_user_stats_report.py
  line_count: 42
  concepts:
    user_account: a registered user of the application
    report: null
  renamings:
    stats: user_stats
  function_nodes:
    - name: get_api_usage
      rename_to: create_api_usage_report
      move_to_file: api/rules/create_api_usage_report.py
      code_unit_type: rule
      concepts:
        auth_token: a token that authenticates a client against the API
      local_terms:
        hash_tag: null
      responsibilities:
        - Collects the API usage of a user account
      steps:
        - Get the auth tokens of the user account
        - Count the API calls per auth token
      extract_method_priority: high
      renamings:
        token: auth_token
      aliases:
        auth_token:
          - token
          - access_token
      abbreviations:
        user_account: ua
      helper_function_nodes:
        - name: _get_api_url
          responsibilities:
            - Builds the URL of the API usage endpoint
          extract_method_priority: n/a
    - name: get_user_stats
      is_helper_candidate: true
      concepts:
        login_name: null
  class_nodes:
    - name: UserStats
      rename_to: UserStatistics
      move_to_file: users/models/user_statistics.py
      code_unit_type: model
      concepts:
        user_stats: the statistics of a user account
      responsibilities:
        - Holds the statistics of a user account
      extract_method_priority: low
      renamings:
        n: nr_of_logins
      method_nodes:
        - name: __str__
          responsibilities:
            - Formats the statistics for display
  variable_nodes:
    - name: MAX_REPORT_LINES
      rename_to: MAX_NR_OF_REPORT_LINES
      move_to_file: myapp/settings.py
      code_unit_type: setting
    - name: DEFAULT_TITLE
"""


def create_env(context: Context):
    return Env(context)


def test_save_module_node_keeps_the_contents_of_a_loaded_node_file(
    context: Context,
):
    # Create the test environment
    env = create_env(context)

    # We have a node file in which every field of the schema is used.
    if env.step(
        env.write_file(
            "reports/markdown_reports.py.breaker.yaml", MARKDOWN_REPORTS_NODE_YAML
        ),
    ):
        pass

    # We load the node file.
    #
    # The module node should reflect the node file.
    if env.step(
        env.load_module_node("reports/markdown_reports.py.breaker.yaml"),
    ):
        assert env.module_node.name == "reports/markdown_reports.py"
        assert env.module_node.concepts == {
            "user_account": "a registered user of the application",
            "report": None,
        }
        get_api_usage_node = env.module_node.function_nodes[0]
        assert get_api_usage_node.aliases == {"auth_token": ["token", "access_token"]}
        assert get_api_usage_node.helper_function_nodes[0].name == "_get_api_url"
        assert env.module_node.class_nodes[0].method_nodes[0].name == "__str__"
        # Fields that are left out of the node file have their default value.
        assert env.module_node.function_nodes[1].rename_to is None
        assert env.module_node.function_nodes[1].helper_function_nodes == []
        assert env.module_node.variable_nodes[0].code_unit_type == "setting"
        assert env.module_node.variable_nodes[1].move_to_file is None
        # An extract-method priority that is not set yet is None, so that it is
        # not confused with 'n/a' (no need to extract methods).
        assert env.module_node.function_nodes[1].extract_method_priority is None

    # We save the module node to a new node file.
    #
    # The new node file should have the same contents as the original one.
    if env.step(
        env.save_module_node("reports/copy.breaker.yaml"),
    ):
        assert env.read_file("reports/copy.breaker.yaml") == MARKDOWN_REPORTS_NODE_YAML


class Env(TestEnv):
    pass
