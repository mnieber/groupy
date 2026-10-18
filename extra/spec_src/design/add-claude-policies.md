## Add the Claude policies

The tests run Groupy with `FakeRfaPolicy` and `FakeRfrPolicy` (`tests/groupy_next_tests/fake_policies.py`), but the
default config refers to `claude_requests.policies.claude_rfa_policy:ClaudeRfaPolicy` and
`claude_requests.policies.claude_rfr_policy:ClaudeRfrPolicy`, which don't exist yet. This plan adds them, so that
`groupy next` can be used on a real code-base.

1. The policies run Claude Code in headless mode (`claude -p`) as a subprocess, in the repo dir.
   1. One subprocess per request, so that every RFA and RFR is a fresh Claude session (as the scenarios assume).
   2. The prompt that Groupy sends is the `prompt` of the request, followed by a fixed preamble that explains how to
      read the context and how to run callbacks (see 2 and 3).
   3. A non-zero exit code of `claude` raises `ClaudeRequestError` (with the request id and the tail of stderr). The
      stage then fails like it does for any other error, so that `groupy next` can resume it.
   4. The output of the session (`--output-format stream-json`) is written to `.groupy/logs/<request-id>.jsonl`, for
      debugging. `groupy init` excludes `.groupy/logs/` from git, like `call-graph.yaml`.
2. The context of a request is written to a file instead of being inlined in the prompt.
   1. Groupy writes `request.context` as yaml to `.groupy/requests/<request-id>/context.yaml` (also excluded from
      git), and the preamble tells Claude to read it.
   2. Values in the context that are models (e.g. the `CallGraphView` of identify-helper-functions) are converted to
      plain dicts with a shared util (`claude_requests/utils/to_plain_data.py`).
3. Claude runs callbacks with a new CLI command: `groupy callback <name> --args '<json>'`.
   1. It calls `run_callback(Callback(name, args), in_rfr=...)` and prints the result as yaml (for the queries
      `get_callers`, `get_callees` and `get_source`), or `OK`.
   2. On an error, it prints the error class and message and exits with code 1. See 4 for what happens next.
   3. The RFR policy sets the env var `GROUPY_IN_RFR=1` for the subprocess, and the command passes
      `in_rfr=True` when it is set. This keeps `CallbackNotAllowedError` working without trusting Claude to pass a
      flag.
4. A failed callback ends the request, and interrupts the stage, as the specs require (s03, and e.g.
   `test_apply_move_steps_to_caller_rejects_a_refactoring_callback`, which expects `CallbackNotAllowedError` from
   `groupy next`). Groupy doesn't kill `claude`, but asks Claude to stop, so that the session ends normally and its
   log is complete.
   1. A failed callback writes the error to `.groupy/requests/<request-id>/error.yaml`: the import path of the
      exception class and the message. `run_callback` has already restored the working tree.
   2. It prints a fixed instruction, e.g. "The callback failed: `<error>`. Stop processing this request: don't run
      more callbacks or edit files, and end your answer."
   3. When the error file exists, every later callback of the request runs nothing, and prints the same
      instruction.
   4. In headless mode, the `claude` process exits when Claude ends its answer. Then the policy restores the working
      tree (which discards the files that Claude edited directly after the failure, in an RFR), recreates the
      exception from the error file, and raises it.
   5. As a safety net, the policy terminates `claude` when it is still running some time (e.g. 5 minutes) after the
      error file was written. If Claude turns out to ignore the instruction, a Claude Code hook (passed with
      `--settings`) can block every tool call once the error file exists.
5. The policies restrict the tools that Claude may use (`--allowedTools`).
   1. `ClaudeRfaPolicy`: `Read`, `Glob`, `Grep` and `Bash(groupy callback:*)`. Claude does not edit files in an RFA;
      all changes go through callbacks.
   2. `ClaudeRfrPolicy`: the same, plus `Edit` and `Write`, since Claude edits the source files in an RFR.
6. The config gets a `claude_model: str` field (default: empty, which means the default model of Claude Code), that
   the policies pass with `--model`. Both policies share the code that builds and runs the command
   (`claude_requests/utils/run_claude.py`).
7. Tests (in a new `claude_policies_tests` package) don't call the real Claude. They put a fake `claude` executable
   on the `PATH` that records its arguments and runs a scripted list of `groupy callback` commands, and check that:
   1. the context file, the preamble, the allowed tools and the model are passed;
   2. callbacks in an RFR run without committing, and a refactoring callback is rejected;
   3. after a failed callback, later callbacks are ignored and get the stop instruction, the working tree is
      restored, and the policy raises the original error;
   4. a failing `claude` raises `ClaudeRequestError`.
8. Out of scope: `ClaudeGroupingPolicy` (the default `grouping_policy`) belongs to smart grouping
   (`add-a-smart-grouping-policy.md`). Until then, the default `grouping_strategy: package` does not use it.

### Open questions

1. Callbacks as a CLI command (above) or as an MCP server (`groupy mcp`) that the policies pass with `--mcp-config`?
   The CLI is simpler and easy to test; MCP gives Claude typed tool schemas for the ~35 callbacks. Recommended: start
   with the CLI, and list the callbacks with their arguments in the preamble.
