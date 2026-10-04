# ModuleNode file example

```yaml
module_node:
  name: reports/markdown_reports.py
  rename_to: reports/rules/create_user_stats_report.py
  concepts: ["user_account"]
  renamings: {}
  function_nodes:
    - name: get_api_usage
      rename_to: create_api_usage_report
      move_to_file: api/rules/create_api_usage_report.py
      concepts: ["auth_token"]
      renamings:
        token: auth_token
        previous_token: previous_auth_token
      helper_function_nodes:
        - name: _get_api_url
          concepts: []
    - name: get_user_stats
      rename_to: create_user_stats_report
      concepts: ["login_name"]
      helper_function_nodes:
        - name: _normalize_login_name
```
